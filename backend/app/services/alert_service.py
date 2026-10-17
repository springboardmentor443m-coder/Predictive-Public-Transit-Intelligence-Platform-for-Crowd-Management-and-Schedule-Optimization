import logging
import re
from datetime import datetime, timezone
from typing import List, Dict, Any, Optional
from sqlalchemy.orm import Session

from app.models.alert import OperationalAlertModel, AlertType, AlertSeverity, AlertStatus
from app.models.trip_update import TripUpdateModel
from app.models.service_alert import ServiceAlertModel
from app.schemas.live_data import DataState
from app.services.ml_service import MLDataService
from app.core.events import manager as ws_manager

logger = logging.getLogger("metroflow.alert_service")


class OperationalAlertService:
    """Core alert generation, deduplication, lifecycle, and notification service."""

    @staticmethod
    def sync_alerts(db: Session) -> Dict[str, int]:
        """
        Evaluates real live data + ML prediction signals, generates deduplicated operational alerts,
        and broadcasts new events over WebSocket.
        """
        now_utc = datetime.now(timezone.utc)
        ml_service = MLDataService.get_instance()
        active_keys_in_cycle = set()
        new_alerts_created = 0

        try:
            # Clean up legacy per-stop LIVE_DELAY alerts and legacy per-bulletin SERVICE_ALERT keys
            legacy_delay_alerts = db.query(OperationalAlertModel).filter(
                OperationalAlertModel.alert_type == AlertType.LIVE_DELAY,
                OperationalAlertModel.alert_key.like("LIVE_DELAY_%_%")  # has route AND stop
            ).all()
            for la in legacy_delay_alerts:
                key_parts = la.alert_key[len("LIVE_DELAY_"):].split("_")
                if len(key_parts) >= 2:  # has stop suffix
                    la.status = AlertStatus.RESOLVED
                    la.updated_at = now_utc
                    la.resolved_at = now_utc

            legacy_bulletin_alerts = db.query(OperationalAlertModel).filter(
                OperationalAlertModel.status == AlertStatus.ACTIVE,
                OperationalAlertModel.alert_key.like("SERVICE_ALERT_%")
            ).all()
            for lba in legacy_bulletin_alerts:
                lba.status = AlertStatus.RESOLVED
                lba.updated_at = now_utc
                lba.resolved_at = now_utc

            if legacy_delay_alerts or legacy_bulletin_alerts:
                db.flush()
                logger.info(f"Resolved {len(legacy_delay_alerts)} legacy delay and {len(legacy_bulletin_alerts)} legacy bulletin alerts.")


            # ----------------------------------------------------
            # 1. OVERCROWDING ALERTS (REAL-TIME ML PREDICTIONS)
            # ----------------------------------------------------
            try:
                live_crowd_data = ml_service.get_realtime_crowd_predictions(db=db)
                station_preds = live_crowd_data.get('predictions', [])
            except Exception as e:
                logger.warning(f"Failed to fetch realtime crowd for alerts: {e}")
                station_preds = []

            station_baselines = ml_service.df_predictions.groupby('station_complex_id')['passenger_count'].mean().to_dict() if ml_service.df_predictions is not None else {}

            for st in station_preds:
                risk = st.get('crowd_risk', 'LOW').upper()
                if risk in ['HIGH', 'CRITICAL']:
                    cid = str(st['station_complex_id'])
                    st_name = st['station_complex']
                    pred_demand = float(st['predicted_next_hour'])
                    obs_demand = float(st.get('latest_passenger_count', pred_demand))
                    baseline = float(station_baselines.get(cid, 1500.0))
                    pressure_ratio = round(pred_demand / max(baseline, 100.0), 2)
                    
                    alert_key = f"OVERCROWD_{cid}"
                    active_keys_in_cycle.add(alert_key)
                    severity = AlertSeverity.CRITICAL if risk == 'CRITICAL' else AlertSeverity.HIGH

                    existing = db.query(OperationalAlertModel).filter(OperationalAlertModel.alert_key == alert_key).first()
                    if existing:
                        existing.severity = severity
                        existing.observed_value = f"{int(obs_demand):,} pax"
                        existing.predicted_value = f"{int(pred_demand):,} pax (next-hr)"
                        existing.threshold_info = f"{pressure_ratio}x baseline ({int(baseline):,} avg)"
                        existing.recommended_action = st.get('recommended_action', 'Monitor station platform flow.')
                        existing.updated_at = now_utc
                        if existing.status == AlertStatus.RESOLVED:
                            existing.status = AlertStatus.ACTIVE
                    else:
                        new_alert = OperationalAlertModel(
                            alert_key=alert_key,
                            alert_type=AlertType.OVERCROWDING,
                            severity=severity,
                            status=AlertStatus.ACTIVE,
                            title=f"Crowd Risk {risk}: {st_name}",
                            description=f"ML demand model forecasts {int(pred_demand):,} passengers next hour ({pressure_ratio}x baseline) at {st_name}.",
                            entity_id=cid,
                            entity_name=st_name,
                            observed_value=f"{int(obs_demand):,} pax",
                            predicted_value=f"{int(pred_demand):,} pax (next-hr)",
                            threshold_info=f"{pressure_ratio}x baseline ({int(baseline):,} avg)",
                            recommended_action=st.get('recommended_action', 'Coordinate platform crowd marshals.'),
                            timestamp=now_utc,
                            updated_at=now_utc,
                            data_state=DataState.PREDICTED
                        )
                        db.add(new_alert)
                        new_alerts_created += 1

            # ----------------------------------------------------
            # 2. LIVE DELAY ALERTS (LIVE MTA GTFS-RT)
            # Deduplicated PER ROUTE (not per stop) to prevent alert explosion.
            # One alert per route that aggregates the worst delay seen.
            # ----------------------------------------------------
            from sqlalchemy import func as sqlfunc
            route_delay_agg = (
                db.query(
                    TripUpdateModel.route_id,
                    sqlfunc.max(TripUpdateModel.delay_seconds).label("max_delay"),
                    sqlfunc.count(TripUpdateModel.stop_id).label("stop_count"),
                )
                .filter(TripUpdateModel.delay_seconds >= 30)
                .group_by(TripUpdateModel.route_id)
                .all()
            )
            for rda in route_delay_agg:
                route_id = rda.route_id or "Subway"
                delay_sec = float(rda.max_delay or 0)
                stop_count = int(rda.stop_count or 1)

                alert_key = f"LIVE_DELAY_{route_id}"
                active_keys_in_cycle.add(alert_key)

                if delay_sec >= 300:
                    severity = AlertSeverity.CRITICAL
                elif delay_sec >= 120:
                    severity = AlertSeverity.HIGH
                elif delay_sec >= 60:
                    severity = AlertSeverity.WARNING
                else:
                    severity = AlertSeverity.INFO

                delay_mins = round(delay_sec / 60, 1)
                existing = db.query(OperationalAlertModel).filter(OperationalAlertModel.alert_key == alert_key).first()
                if existing:
                    existing.severity = severity
                    existing.observed_value = f"Max {int(delay_sec)}s ({delay_mins} min), {stop_count} stops affected"
                    existing.updated_at = now_utc
                    if existing.status == AlertStatus.RESOLVED:
                        existing.status = AlertStatus.ACTIVE
                else:
                    new_alert = OperationalAlertModel(
                        alert_key=alert_key,
                        alert_type=AlertType.LIVE_DELAY,
                        severity=severity,
                        status=AlertStatus.ACTIVE,
                        title=f"Live GTFS-RT Delay: Line {route_id}",
                        description=f"MTA GTFS-RT reports max delay of {int(delay_sec)}s ({delay_mins} min) on Line {route_id} across {stop_count} affected stops.",
                        entity_id=route_id,
                        entity_name=f"Line {route_id}",
                        observed_value=f"Max {int(delay_sec)}s ({delay_mins} min), {stop_count} stops",
                        predicted_value="Live Delay Severity Model Active",
                        threshold_info="Threshold >= 30s delay (per route)",
                        recommended_action=f"Monitor Line {route_id} headway; coordinate standby train insertion at transfer hubs.",
                        timestamp=now_utc,
                        updated_at=now_utc,
                        data_state=DataState.LIVE
                    )
                    db.add(new_alert)
                    new_alerts_created += 1

            # ----------------------------------------------------
            # 3. SERVICE ALERTS (CONSOLIDATED PER ROUTE FROM LIVE MTA GTFS-RT)
            # Group the 188+ raw bulletins by line to prevent alert spam
            # and surface high-signal operational advisories.
            # ----------------------------------------------------
            service_alerts = db.query(ServiceAlertModel).filter(ServiceAlertModel.active == True).all()

            route_bulletins = {}
            for sa in service_alerts:
                routes = sa.affected_routes or ["System"]
                for r in set(routes):
                    if r not in route_bulletins:
                        route_bulletins[r] = []
                    route_bulletins[r].append(sa)

            for route_id, b_list in route_bulletins.items():
                alert_key = f"SERVICE_ROUTE_{route_id}"
                active_keys_in_cycle.add(alert_key)
                count = len(b_list)

                all_text = " ".join([(b.header_text or "") + " " + (b.description_text or "") for b in b_list]).lower()
                if "suspended" in all_text or "no service" in all_text or "no [" in all_text:
                    severity = AlertSeverity.CRITICAL
                elif "delay" in all_text or "slow" in all_text or "skip" in all_text:
                    severity = AlertSeverity.HIGH
                else:
                    severity = AlertSeverity.WARNING

                top_bulletin = b_list[0] if b_list else None
                raw_snippet = top_bulletin.header_text[:120] if top_bulletin and top_bulletin.header_text else "Service bulletin active"
                clean_snippet = re.sub(r'\[.*?icon.*?\]', '', raw_snippet, flags=re.IGNORECASE).strip()
                clean_snippet = re.sub(r'\[\s*([A-Za-z0-9]+)\s*\]', r'Line \1', clean_snippet)
                clean_snippet = re.sub(r'\s+', ' ', clean_snippet).strip()
                if not clean_snippet:
                    clean_snippet = "Service bulletin active"

                existing = db.query(OperationalAlertModel).filter(OperationalAlertModel.alert_key == alert_key).first()
                if existing:
                    existing.severity = severity
                    existing.observed_value = f"{count} active bulletin{'s' if count > 1 else ''}"
                    existing.description = f"MTA reports {count} active operational notices for Line {route_id}. Primary: {clean_snippet}"
                    existing.updated_at = now_utc
                    if existing.status == AlertStatus.RESOLVED:
                        existing.status = AlertStatus.ACTIVE
                else:
                    new_alert = OperationalAlertModel(
                        alert_key=alert_key,
                        alert_type=AlertType.SERVICE_ALERT,
                        severity=severity,
                        status=AlertStatus.ACTIVE,
                        title=f"Line {route_id} Advisory: {count} active bulletin{'s' if count > 1 else ''}",
                        description=f"MTA reports {count} active operational notices for Line {route_id}. Primary: {clean_snippet}",
                        entity_id=route_id,
                        entity_name=f"Line {route_id}",
                        observed_value=f"{count} active bulletin{'s' if count > 1 else ''}",
                        predicted_value="Live MTA Bulletin Feed",
                        threshold_info=f"Active notices: {count}",
                        recommended_action=f"Advise Line {route_id} operators; coordinate passenger platform information.",
                        timestamp=now_utc,
                        updated_at=now_utc,
                        data_state=DataState.LIVE
                    )
                    db.add(new_alert)
                    new_alerts_created += 1

            # ----------------------------------------------------
            # 4. NETWORK IMPACT ALERTS (DYNAMIC GRAPH NETWORK CONGESTION)
            # ----------------------------------------------------
            net_risks = ml_service.get_network_risk(db=db)
            for nr in net_risks:
                if nr.get('network_pressure_ratio', 1.0) >= 1.2 or nr.get('network_risk') in ['HIGH', 'CRITICAL']:
                    cid = nr['station_complex_id']
                    st_name = nr['station_complex']
                    ratio = nr['network_pressure_ratio']
                    risk = nr['network_risk']
                    factors = ", ".join(nr.get('contributing_factors', []))
                    
                    alert_key = f"NETWORK_IMPACT_{cid}"
                    active_keys_in_cycle.add(alert_key)
                    severity = AlertSeverity.CRITICAL if risk == 'CRITICAL' else AlertSeverity.HIGH

                    existing = db.query(OperationalAlertModel).filter(OperationalAlertModel.alert_key == alert_key).first()
                    if existing:
                        existing.severity = severity
                        existing.predicted_value = f"{ratio}x network pressure ratio"
                        existing.updated_at = now_utc
                        if existing.status == AlertStatus.RESOLVED:
                            existing.status = AlertStatus.ACTIVE
                    else:
                        new_alert = OperationalAlertModel(
                            alert_key=alert_key,
                            alert_type=AlertType.NETWORK_IMPACT,
                            severity=severity,
                            status=AlertStatus.ACTIVE,
                            title=f"Network Congestion Propagation: {st_name}",
                            description=f"Connected-station congestion model predicts network pressure ratio of {ratio}x propagating to adjacent transfer nodes. Factors: {factors}.",
                            entity_id=cid,
                            entity_name=st_name,
                            observed_value=f"{int(nr['predicted_next_hour']):,} pax forecast",
                            predicted_value=f"{ratio}x network pressure ratio",
                            threshold_info=f"Contributing factors: {factors}",
                            recommended_action=nr['recommended_action'],
                            timestamp=now_utc,
                            updated_at=now_utc,
                            data_state=DataState.PREDICTED
                        )
                        db.add(new_alert)
                        new_alerts_created += 1

            # ----------------------------------------------------
            # 5. RESOLVE INACTIVE ALERTS (LIFECYCLE)
            # ----------------------------------------------------
            all_active_db_alerts = db.query(OperationalAlertModel).filter(
                OperationalAlertModel.status.in_([AlertStatus.ACTIVE, AlertStatus.ACKNOWLEDGED])
            ).all()

            resolved_count = 0
            for db_alert in all_active_db_alerts:
                if db_alert.alert_key not in active_keys_in_cycle:
                    db_alert.status = AlertStatus.RESOLVED
                    db_alert.updated_at = now_utc
                    resolved_count += 1

            db.commit()

            logger.info(
                f"Alert sync cycle complete: {new_alerts_created} new alerts, "
                f"{resolved_count} resolved alerts. Active keys: {len(active_keys_in_cycle)}"
            )

            return {
                "active_count": len(active_keys_in_cycle),
                "created_count": new_alerts_created,
                "resolved_count": resolved_count
            }

        except Exception as e:
            db.rollback()
            logger.error(f"Error during alert sync cycle: {e}")
            return {"error": str(e)}

    @staticmethod
    def get_active_alerts(db: Session, severity: Optional[str] = None, alert_type: Optional[str] = None) -> List[OperationalAlertModel]:
        """Retrieve all currently active or acknowledged operational alerts."""
        query = db.query(OperationalAlertModel).filter(
            OperationalAlertModel.status.in_([AlertStatus.ACTIVE, AlertStatus.ACKNOWLEDGED])
        )
        if severity:
            query = query.filter(OperationalAlertModel.severity == severity.upper())
        if alert_type:
            query = query.filter(OperationalAlertModel.alert_type == alert_type.upper())
        
        # Order by severity rank and timestamp descending
        alerts = query.order_by(OperationalAlertModel.timestamp.desc()).all()
        return alerts

    @staticmethod
    def get_alert_history(db: Session, limit: int = 100) -> List[OperationalAlertModel]:
        """Retrieve operational alert history including resolved events."""
        return db.query(OperationalAlertModel).order_by(OperationalAlertModel.updated_at.desc()).limit(limit).all()

    @staticmethod
    def get_summary(db: Session) -> Dict[str, int]:
        """Compute alert metrics for dashboard KPI cards."""
        active_alerts = OperationalAlertModel.get_active_alerts(db) if hasattr(OperationalAlertModel, 'get_active_alerts') else db.query(OperationalAlertModel).filter(
            OperationalAlertModel.status.in_([AlertStatus.ACTIVE, AlertStatus.ACKNOWLEDGED])
        ).all()

        crit = sum(1 for a in active_alerts if a.severity == AlertSeverity.CRITICAL)
        high = sum(1 for a in active_alerts if a.severity == AlertSeverity.HIGH)
        warn = sum(1 for a in active_alerts if a.severity == AlertSeverity.WARNING)
        info = sum(1 for a in active_alerts if a.severity == AlertSeverity.INFO)
        
        live_delays = sum(1 for a in active_alerts if a.alert_type == AlertType.LIVE_DELAY)
        overcrowd = sum(1 for a in active_alerts if a.alert_type == AlertType.OVERCROWDING)
        service = sum(1 for a in active_alerts if a.alert_type == AlertType.SERVICE_ALERT)
        network = sum(1 for a in active_alerts if a.alert_type == AlertType.NETWORK_IMPACT)

        return {
            "total_active": len(active_alerts),
            "critical_count": crit,
            "high_count": high,
            "warning_count": warn,
            "info_count": info,
            "live_delays_count": live_delays,
            "overcrowding_count": overcrowd,
            "service_alerts_count": service,
            "network_impact_count": network
        }

    @staticmethod
    def acknowledge_alert(db: Session, alert_id: int, user_email: str) -> Optional[OperationalAlertModel]:
        """Acknowledge an operational alert, updating its status to ACKNOWLEDGED."""
        alert = db.query(OperationalAlertModel).filter(OperationalAlertModel.id == alert_id).first()
        if not alert:
            return None

        now_utc = datetime.now(timezone.utc)
        alert.status = AlertStatus.ACKNOWLEDGED
        alert.acknowledged_by = user_email
        alert.acknowledged_at = now_utc
        alert.updated_at = now_utc
        db.commit()
        db.refresh(alert)
        return alert
