import logging
import uuid
from datetime import datetime, timedelta

from sqlalchemy.orm import Session

from app.models.alert import Alert
from app.schemas.alert import AlertBroadcast
from app.services import socketio_state

logger = logging.getLogger(__name__)

OVERCROWDING_PCT = 90
CRITICAL_PCT = 100


def _new_alert_id(prefix: str) -> str:
    """Collision-free alert ID: prefix + short random suffix."""
    return f"{prefix}-{uuid.uuid4().hex[:12]}"


def _alert_to_dict(alert: Alert) -> dict:
    return {
        "id": alert.id,
        "type": alert.type,
        "severity": alert.severity,
        "station_id": alert.station_id,
        "train_id": alert.train_id,
        "title": alert.title,
        "message": alert.message,
        "is_acknowledged": alert.is_acknowledged,
        "created_at": alert.created_at.isoformat() if alert.created_at else None,
        "resolved_at": alert.resolved_at.isoformat() if alert.resolved_at else None,
    }


def evaluate_alerts(db: Session) -> list[dict]:
    """Rule engine: raises overcrowding alerts from live occupancy snapshots."""
    from app.services.crowd_service import get_all_live_snapshots

    created: list[dict] = []
    snapshots = get_all_live_snapshots(db)
    now = datetime.utcnow()

    for snap in snapshots:
        pct = snap["occupancy_pct"]
        if pct < OVERCROWDING_PCT:
            continue
        severity = "critical" if pct >= CRITICAL_PCT else "high"

        duplicate = (
            db.query(Alert)
            .filter(
                Alert.type == "overcrowding",
                Alert.station_id == snap["station_id"],
                Alert.is_acknowledged.is_(False),
                Alert.created_at >= now - timedelta(minutes=15),
            )
            .first()
        )
        if duplicate:
            continue

        alert = Alert(
            id=_new_alert_id(f"ALR-OCC-{snap['station_id']}"),
            type="overcrowding",
            severity=severity,
            station_id=snap["station_id"],
            title=f"High congestion at {snap['station_name']}",
            message=(
                f"Platform occupancy reached {snap['occupancy_pct']}% "
                f"({snap['congestion_level']} congestion). "
                f"Inflow {snap['inflow_rate']}/min vs outflow {snap['outflow_rate']}/min. "
                f"Recommend reducing train headway."
            ),
        )
        db.add(alert)
        db.commit()
        db.refresh(alert)
        created.append(_alert_to_dict(alert))
        logger.warning(f"Overcrowding alert raised for {snap['station_name']} ({pct}%)")

    return created


def raise_delay_alert(db: Session, schedule, delay_min: int) -> Alert:
    """Creates a delay notification alert for a reported schedule delay."""
    severity = "high" if delay_min >= 10 else "medium" if delay_min >= 5 else "low"
    alert = Alert(
        id=_new_alert_id(f"ALR-DLY-{schedule.id}"),
        type="delay",
        severity=severity,
        station_id=schedule.station_id,
        train_id=schedule.train_id,
        title=f"Train {schedule.train_id} running {delay_min} min late",
        message=(
            f"Service {schedule.train_id} ({schedule.direction}) at {schedule.station_id} "
            f"is delayed by {delay_min} minutes. Status: {schedule.status}."
        ),
    )
    db.add(alert)
    db.commit()
    db.refresh(alert)
    return alert


def list_alerts(db: Session, acknowledged: bool | None = None, limit: int = 100) -> list[Alert]:
    q = db.query(Alert).order_by(Alert.created_at.desc())
    if acknowledged is not None:
        q = q.filter(Alert.is_acknowledged.is_(acknowledged))
    return q.limit(limit).all()


def acknowledge_alert(db: Session, alert_id: str) -> Alert:
    from fastapi import HTTPException

    alert = db.query(Alert).filter(Alert.id == alert_id).first()
    if not alert:
        raise HTTPException(status_code=404, detail="Alert not found")
    alert.is_acknowledged = True
    alert.resolved_at = datetime.utcnow()
    db.add(alert)
    db.commit()
    db.refresh(alert)
    return alert


def broadcast_alert(db: Session, payload: AlertBroadcast) -> Alert:
    alert = Alert(
        id=_new_alert_id("ALR-BC"),
        type=payload.type,
        severity=payload.severity,
        station_id=payload.station_id,
        title=payload.title,
        message=payload.message,
    )
    db.add(alert)
    db.commit()
    db.refresh(alert)

    sio = socketio_state.get_sio()
    if sio is not None:
        try:
            import asyncio

            asyncio.ensure_future(sio.emit("alert", _alert_to_dict(alert)))
        except Exception as e:
            logger.warning(f"socket emit failed: {e}")
    return alert


def recent_unbroadcast_alerts(db: Session, within_seconds: int = 12) -> list[dict]:
    cutoff = datetime.utcnow() - timedelta(seconds=within_seconds)
    rows = (
        db.query(Alert)
        .filter(Alert.created_at >= cutoff)
        .order_by(Alert.created_at.asc())
        .all()
    )
    return [_alert_to_dict(a) for a in rows]
