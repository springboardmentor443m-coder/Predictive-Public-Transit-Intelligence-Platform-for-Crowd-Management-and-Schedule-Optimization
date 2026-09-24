"""Real-time train monitoring derived from the live timetable.

Each train's live telemetry (position, status, ETA, projected load) is
reconstructed from its scheduled stops around the current time — no separate
sensor pipeline is required. The Socket.IO broadcast loop refreshes these
snapshots every few seconds, so dashboards animate trains as they progress
between stations.
"""

import logging
from datetime import datetime, timedelta

from sqlalchemy.orm import Session

from app.core.time import utcnow

from app.models.schedule import TrainSchedule
from app.models.station import Station
from app.models.train import Train

logger = logging.getLogger(__name__)

_DWELL_SECONDS = 45.0
_HISTORY_LOOKBACK_HOURS = 3
_FORWARD_LOOKAHEAD_HOURS = 18


def _cached_crowd(station_id: str) -> dict | None:
    """Best-effort read of the live crowd snapshot cache for load projection."""
    try:
        from app.core.cache import cache_get

        return cache_get(f"crowd:latest:{station_id}")
    except Exception:
        return None


def _station_name(station_names: dict, station_id: str | None) -> str | None:
    if not station_id:
        return None
    st = station_names.get(station_id)
    return st.name if st else station_id


def _collect_schedules(db: Session, train_id: str | None = None) -> list[TrainSchedule]:
    q = db.query(TrainSchedule).filter(
        TrainSchedule.arrival >= utcnow() - timedelta(hours=_HISTORY_LOOKBACK_HOURS),
        TrainSchedule.arrival <= utcnow() + timedelta(hours=_FORWARD_LOOKAHEAD_HOURS),
    )
    if train_id:
        q = q.filter(TrainSchedule.train_id == train_id)
    return q.order_by(TrainSchedule.arrival.asc()).all()


def _compute_train(train: Train, schedules: list[TrainSchedule], station_names: dict, now: datetime) -> dict:
    upcoming = [s for s in schedules if s.arrival >= now]
    past = [s for s in schedules if s.arrival < now]

    prev = past[-1] if past else None
    nxt = upcoming[0] if upcoming else None
    ref = nxt or prev

    line = None
    if ref is not None:
        st = station_names.get(ref.station_id)
        line = st.line if st else (ref.station.line if ref.station else None)
    direction = ref.direction if ref is not None else None

    next_eta_min = None
    next_arrival = None
    headway_min = None
    delay_min = 0
    position_pct = 0.0
    status = "out_of_service"

    if nxt is not None:
        headway_min = nxt.headway_min
        delay_min = nxt.delay_min or 0
        next_eta_min = max(0.0, (nxt.arrival - now).total_seconds() / 60.0)
        next_arrival = nxt.arrival.isoformat() + "Z"

        if delay_min > 2:
            status = "delayed"
        elif prev is None:
            status = "awaiting_departure"
        else:
            span = (nxt.arrival - prev.arrival).total_seconds()
            elapsed = max(0.0, (now - prev.arrival).total_seconds())
            if elapsed <= _DWELL_SECONDS:
                status = "at_station"
                position_pct = 0.0
            else:
                status = "in_transit"
                position_pct = min(100.0, max(0.0, (elapsed - _DWELL_SECONDS) / max(1.0, span - _DWELL_SECONDS) * 100.0))
    elif prev is not None:
        status = "at_terminal" if train.status == "active" else "out_of_service"
        position_pct = 100.0

    if train.status == "maintenance":
        status = "in_depot"
        position_pct = 0.0

    current_station_id = prev.station_id if prev else None
    next_station_id = nxt.station_id if nxt else None

    # Projected load: blend cached crowd snapshots of current + next stations.
    loads = []
    for sid in (current_station_id, next_station_id):
        if sid:
            snap = _cached_crowd(sid)
            if snap and snap.get("occupancy_pct") is not None:
                loads.append(float(snap["occupancy_pct"]))
    load_pct = round(sum(loads) / len(loads), 1) if loads else None

    return {
        "train_id": train.id,
        "code": train.code,
        "model": train.model,
        "capacity": train.capacity,
        "line": line,
        "status": status,
        "current_station": (
            {"id": current_station_id, "name": _station_name(station_names, current_station_id)}
            if current_station_id
            else None
        ),
        "next_station": (
            {"id": next_station_id, "name": _station_name(station_names, next_station_id)}
            if next_station_id
            else None
        ),
        "direction": direction,
        "position_pct": round(position_pct, 1),
        "headway_min": headway_min,
        "delay_min": delay_min,
        "next_eta_min": round(next_eta_min, 1) if next_eta_min is not None else None,
        "next_arrival": next_arrival,
        "load_pct": load_pct,
        "last_updated": now.isoformat() + "Z",
    }


def get_live_trains(db: Session) -> list[dict]:
    """Live telemetry for every train in the network."""
    trains = db.query(Train).all()
    if not trains:
        return []
    station_names = {s.id: s for s in db.query(Station).all()}
    by_train: dict[str, list[TrainSchedule]] = {}
    for s in _collect_schedules(db):
        by_train.setdefault(s.train_id, []).append(s)
    now = utcnow()
    return [
        _compute_train(t, by_train.get(t.id, []), station_names, now)
        for t in trains
    ]


def get_live_train(db: Session, train_id: str) -> dict | None:
    train = db.query(Train).filter(Train.id == train_id).first()
    if train is None:
        return None
    station_names = {s.id: s for s in db.query(Station).all()}
    return _compute_train(train, _collect_schedules(db, train_id), station_names, utcnow())


def upcoming_schedule(db: Session, train_id: str, limit: int = 50) -> list[dict]:
    """Future timetable entries for a train (for the train detail panel)."""
    rows = (
        db.query(TrainSchedule)
        .filter(
            TrainSchedule.train_id == train_id,
            TrainSchedule.arrival >= utcnow(),
        )
        .order_by(TrainSchedule.arrival.asc())
        .limit(limit)
        .all()
    )
    return [
        {
            "id": s.id,
            "station_id": s.station_id,
            "station_name": s.station.name if s.station else s.station_id,
            "direction": s.direction,
            "arrival": s.arrival.isoformat() + "Z",
            "departure": s.departure.isoformat() + "Z",
            "headway_min": s.headway_min,
            "status": s.status,
            "delay_min": s.delay_min or 0,
            "is_peak": s.is_peak,
        }
        for s in rows
    ]