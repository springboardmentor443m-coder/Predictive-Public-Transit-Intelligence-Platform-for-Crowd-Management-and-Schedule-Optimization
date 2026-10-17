import asyncio
import logging
from datetime import datetime, timezone, timedelta
from typing import Optional
from sqlalchemy.orm import Session

from app.core.database import SessionLocal
from app.core.events import manager as ws_manager
from app.services.live_data.mta_subway import MTASubwayLiveDataProvider
from app.models.vehicle import TransitVehicle
from app.models.trip_update import TripUpdateModel
from app.models.service_alert import ServiceAlertModel
from app.models.feed_status import FeedStatusModel, HealthStatus
from app.schemas.live_data import DataState
from app.services.alert_service import OperationalAlertService

logger = logging.getLogger("metroflow.ingestion")

mta_provider = MTASubwayLiveDataProvider()


class LiveDataIngestionService:
    """Background ingestion loop fetching, persisting, and broadcasting MTA subway live data."""

    def __init__(self, polling_interval_seconds: int = 30):
        self.polling_interval = polling_interval_seconds
        self.is_running = False
        self._task: Optional[asyncio.Task] = None

    async def sync_once(self, db: Optional[Session] = None) -> dict:
        """Fetch live MTA feed, update DB models, and broadcast real-time WebSocket events."""
        close_session = False
        if db is None:
            db = SessionLocal()
            close_session = True

        try:
            logger.info("Executing live MTA Subway GTFS-RT ingestion cycle...")
            vehicles, trips, alerts = await mta_provider.fetch_all_normalized_entities()
            status = mta_provider.get_status()

            now_utc = datetime.now(timezone.utc)

            # 1. Persist/Update Vehicles in DB
            for v in vehicles[:150]:  # Cap at active operational trains
                existing = db.query(TransitVehicle).filter(TransitVehicle.vehicle_id == v.vehicle_id).first()
                if existing:
                    existing.trip_id = v.trip_id
                    existing.route_id = v.route_id
                    existing.direction_id = v.direction_id
                    existing.current_stop_id = v.current_stop_id
                    existing.current_stop_sequence = v.current_stop_sequence
                    existing.current_status = v.current_status
                    existing.latitude = v.latitude
                    existing.longitude = v.longitude
                    existing.bearing = v.bearing
                    existing.timestamp = v.timestamp
                    existing.updated_at = now_utc
                else:
                    db.add(
                        TransitVehicle(
                            vehicle_id=v.vehicle_id,
                            trip_id=v.trip_id,
                            route_id=v.route_id,
                            direction_id=v.direction_id,
                            current_stop_id=v.current_stop_id,
                            current_stop_sequence=v.current_stop_sequence,
                            current_status=v.current_status,
                            latitude=v.latitude,
                            longitude=v.longitude,
                            bearing=v.bearing,
                            timestamp=v.timestamp,
                            data_state=DataState.LIVE
                        )
                    )

            # 2. Persist/Update TripUpdates in DB
            db.query(TripUpdateModel).delete()  # Replace current active trip updates
            for tu in trips[:300]:
                db.add(
                    TripUpdateModel(
                        trip_id=tu.trip_id,
                        route_id=tu.route_id,
                        stop_id=tu.stop_id,
                        delay_seconds=tu.delay_seconds,
                        estimated_arrival=tu.estimated_arrival,
                        estimated_departure=tu.estimated_departure,
                        timestamp=tu.timestamp,
                        data_state=DataState.LIVE
                    )
                )

            # 3. Persist/Update ServiceAlerts in DB (full reconciliation)
            live_alert_ids = {alt.alert_id for alt in alerts}

            # Mark any previously active alert that is no longer in the live feed as inactive
            stale_alerts = db.query(ServiceAlertModel).filter(
                ServiceAlertModel.active == True,
                ~ServiceAlertModel.alert_id.in_(live_alert_ids)
            ).all()
            for stale in stale_alerts:
                stale.active = False

            # Upsert all live alerts (insert new, reactivate existing)
            for alt in alerts:
                existing_alert = db.query(ServiceAlertModel).filter(ServiceAlertModel.alert_id == alt.alert_id).first()
                if existing_alert:
                    existing_alert.header_text = alt.header_text
                    existing_alert.description_text = alt.description_text
                    existing_alert.affected_routes = alt.affected_routes
                    existing_alert.affected_stops = alt.affected_stops
                    existing_alert.active = True
                    existing_alert.timestamp = alt.timestamp
                else:
                    db.add(
                        ServiceAlertModel(
                            alert_id=alt.alert_id,
                            header_text=alt.header_text,
                            description_text=alt.description_text,
                            affected_routes=alt.affected_routes,
                            affected_stops=alt.affected_stops,
                            start_time=alt.start_time,
                            end_time=alt.end_time,
                            active=alt.active,
                            timestamp=alt.timestamp,
                            data_state=DataState.LIVE
                        )
                    )

            # 4. Record FeedStatus Record
            health_enum = mta_provider.last_status
            status_entry = FeedStatusModel(
                provider_name=mta_provider.provider_name,
                feed_timestamp=mta_provider.last_feed_timestamp,
                received_at=now_utc,
                latency_ms=mta_provider.last_latency_ms,
                entity_count=len(vehicles) + len(trips) + len(alerts),
                status=health_enum,
                error_message=mta_provider.last_error
            )
            db.add(status_entry)
            db.commit()

            # 5. Evaluate & Sync Operational Alerts (Deduplicated Lifecycle)
            alert_result = OperationalAlertService.sync_alerts(db)

            # 6. Broadcast Normalized Events via WebSocket Infrastructure
            summary_payload = {
                "event": "feed.status",
                "data_state": "LIVE",
                "timestamp": now_utc.isoformat(),
                "payload": {
                    "provider": mta_provider.provider_name,
                    "status": health_enum.value,
                    "latency_ms": mta_provider.last_latency_ms,
                    "vehicles_count": len(vehicles),
                    "trips_count": len(trips),
                    "alerts_count": len(alerts),
                    "active_alerts_count": alert_result.get("active_count", 0),
                    "last_sync": now_utc.isoformat()
                }
            }
            await ws_manager.broadcast(summary_payload)

            # 6b. Broadcast live vehicle positions for real-time map updates (Fix #3)
            # Sends compact diffs so frontend can update markers without HTTP polling
            vehicle_positions = [
                {
                    "vehicle_id": v.vehicle_id,
                    "route_id": v.route_id,
                    "trip_id": v.trip_id,
                    "stop_id": v.current_stop_id,
                    "status": v.current_status,
                    "lat": v.latitude,
                    "lon": v.longitude,
                    "bearing": v.bearing,
                }
                for v in vehicles[:150]
                if v.latitude and v.longitude  # Only emit vehicles with real GPS coords
            ]
            if vehicle_positions:
                await ws_manager.broadcast({
                    "event": "vehicles.update",
                    "data_state": "LIVE",
                    "timestamp": now_utc.isoformat(),
                    "payload": {
                        "count": len(vehicle_positions),
                        "vehicles": vehicle_positions,
                    }
                })
            
            # Also broadcast compact trip delay summary for map risk overlay
            delay_summary: dict = {}
            for tu in trips[:300]:
                if tu.route_id and tu.delay_seconds and tu.delay_seconds > 60:
                    if tu.route_id not in delay_summary or delay_summary[tu.route_id] < tu.delay_seconds:
                        delay_summary[tu.route_id] = tu.delay_seconds
            if delay_summary:
                await ws_manager.broadcast({
                    "event": "delays.update",
                    "data_state": "LIVE",
                    "timestamp": now_utc.isoformat(),
                    "payload": {"route_delays": delay_summary}
                })

            if alert_result.get("created_count", 0) > 0 or alert_result.get("resolved_count", 0) > 0:
                alert_payload = {
                    "event": "alert.update",
                    "data_state": "LIVE/PREDICTED",
                    "timestamp": now_utc.isoformat(),
                    "payload": alert_result
                }
                await ws_manager.broadcast(alert_payload)

            logger.info(
                f"MTA Ingestion finished: {len(vehicles)} vehicles, {len(trips)} trip updates, "
                f"{len(alerts)} alerts. Health: {health_enum.value}. Active operational alerts: {alert_result.get('active_count', 0)}"
            )

            return {
                "status": "success",
                "vehicles_count": len(vehicles),
                "trips_count": len(trips),
                "alerts_count": len(alerts),
                "health": health_enum.value,
                "latency_ms": mta_provider.last_latency_ms
            }
        except Exception as e:
            if db:
                db.rollback()
            logger.error(f"Error during ingestion cycle: {e}")
            return {"status": "error", "message": str(e)}
        finally:
            if close_session and db:
                db.close()

    async def _cleanup_old_records(self):
        """Purge resolved alerts and stale DB rows to prevent unbounded growth."""
        try:
            from app.models.alert import OperationalAlertModel, AlertStatus
            from app.models.feed_status import FeedStatusModel
            db = SessionLocal()
            now_utc = datetime.now(timezone.utc)
            cutoff_24h = now_utc - timedelta(hours=24)
            cutoff_48h = now_utc - timedelta(hours=48)
            cutoff_7d  = now_utc - timedelta(days=7)

            # Delete resolved operational alerts older than 24h
            deleted_op = db.query(OperationalAlertModel).filter(
                OperationalAlertModel.status == AlertStatus.RESOLVED,
                OperationalAlertModel.updated_at < cutoff_24h
            ).delete(synchronize_session=False)

            # Delete inactive service alerts older than 48h
            deleted_sa = db.query(ServiceAlertModel).filter(
                ServiceAlertModel.active == False,
                ServiceAlertModel.timestamp < cutoff_48h
            ).delete(synchronize_session=False)

            # Keep only last 7 days of feed status records
            deleted_fs = db.query(FeedStatusModel).filter(
                FeedStatusModel.received_at < cutoff_7d
            ).delete(synchronize_session=False)

            db.commit()
            db.close()
            logger.info(
                f"DB cleanup: removed {deleted_op} old resolved alerts, "
                f"{deleted_sa} stale service alerts, {deleted_fs} old feed status records."
            )
        except Exception as e:
            logger.error(f"Error during DB cleanup: {e}")

    async def _loop(self):
        logger.info(f"Starting background live MTA ingestion loop (interval: {self.polling_interval}s)")
        self.is_running = True
        consecutive_failures = 0
        cycle_count = 0
        while self.is_running:
            try:
                res = await self.sync_once()
                if res.get("status") == "success":
                    consecutive_failures = 0
                    cycle_count += 1
                else:
                    consecutive_failures += 1
            except Exception as e:
                logger.error(f"Unhandled error in ingestion loop: {e}")
                consecutive_failures += 1

            # Run DB cleanup every 30 cycles (~15 minutes at 30s interval)
            if cycle_count > 0 and cycle_count % 30 == 0:
                await self._cleanup_old_records()
            
            # Bounded exponential backoff: max 5 mins (300s)
            backoff_interval = min(self.polling_interval * (2 ** min(consecutive_failures, 5)), 300) if consecutive_failures > 0 else self.polling_interval
            if consecutive_failures > 0:
                logger.warning(f"Ingestion failed. Backing off for {backoff_interval}s...")
            
            await asyncio.sleep(backoff_interval)

    def start(self):
        if not self.is_running:
            self._task = asyncio.create_task(self._loop())

    def stop(self):
        self.is_running = False
        if self._task:
            self._task.cancel()


ingestion_service = LiveDataIngestionService()
