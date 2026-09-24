import logging
import random
from datetime import datetime, timedelta

from app.core.time import utcnow

from sqlalchemy.orm import Session

from app.core.cache import cache_get, cache_set
from app.ml import features as feat
from app.models.ridership import RidershipRecord
from app.models.station import Station
from app.schemas.crowd import LiveCrowdSnapshot, StationHeatmapPoint, StationHistoryPoint

logger = logging.getLogger(__name__)

CONGESTION_THRESHOLD_LOW = 0.55
CONGESTION_THRESHOLD_MED = 0.75
CONGESTION_THRESHOLD_HIGH = 0.90

_SENSOR_SAMPLE_RATE = 0.2
_HEATMAP_SAMPLE_WINDOW = 30


def log_sensor_event(snapshot: dict) -> None:
    """Persists a density snapshot into MongoDB (best-effort, sampled)."""
    try:
        if snapshot.get("congestion_level") == "low" and random.random() > _SENSOR_SAMPLE_RATE:
            return
        from app.core.mongo import insert_sensor_event

        insert_sensor_event({
            "event_type": "density_snapshot",
            "station_id": snapshot.get("station_id"),
            "station_name": snapshot.get("station_name"),
            "line": snapshot.get("line"),
            "occupancy": snapshot.get("occupancy"),
            "capacity": snapshot.get("capacity"),
            "occupancy_pct": snapshot.get("occupancy_pct"),
            "congestion_level": snapshot.get("congestion_level"),
            "inflow_per_min": snapshot.get("inflow_rate"),
            "outflow_per_min": snapshot.get("outflow_rate"),
            "recorded_at": utcnow(),
        })
    except Exception as e:
        logger.debug(f"sensor event log skipped: {e}")


def compute_congestion_level(pct_float: float) -> str:
    if pct_float >= CONGESTION_THRESHOLD_HIGH:
        return "critical"
    if pct_float >= CONGESTION_THRESHOLD_MED:
        return "high"
    if pct_float >= CONGESTION_THRESHOLD_LOW:
        return "medium"
    return "low"


def get_live_snapshot(db: Session, station_id: str) -> dict:
    now = utcnow()
    key = f"crowd:latest:{station_id}"
    cached = cache_get(key)
    if cached:
        return cached

    station = db.query(Station).filter(Station.id == station_id).first()
    if not station:
        return None

    rec = (
        db.query(RidershipRecord)
        .filter(RidershipRecord.station_id == station_id)
        .filter(RidershipRecord.timestamp <= now)
        .order_by(RidershipRecord.timestamp.desc())
        .first()
    )

    if rec:
        entries = rec.entries
        exits = rec.exits
        occupancy = rec.occupancy
        congestion = rec.congestion_level
    else:
        hour = now.hour
        weekday = now.weekday()
        baseline_pct = feat.station_baseline_occupancy_pct(hour)
        if weekday >= 5:
            baseline_pct *= feat.WEEKEND_FACTOR
        peak_mult = feat.PEAK_MULTIPLIER.get(hour, 1.0)
        baseline_pct *= 1 + (peak_mult - 1) * 0.5
        baseline_pct = min(1.0, baseline_pct)
        occupancy = int(station.capacity_per_hour * baseline_pct)
        per_min = int(baseline_pct * station.capacity_per_hour / 60)
        entries, exits = per_min, per_min
        congestion = compute_congestion_level(baseline_pct)

    occupancy_pct = round(min(1.0, occupancy / max(1, station.capacity_per_hour)) * 100, 1)
    inflow_rate = round(entries / 15.0, 1)
    outflow_rate = round(exits / 15.0, 1)

    snapshot = {
        "station_id": station.id,
        "station_name": station.name,
        "line": station.line,
        "occupancy": occupancy,
        "capacity": station.capacity_per_hour,
        "occupancy_pct": occupancy_pct,
        "congestion_level": congestion,
        "inflow_rate": inflow_rate,
        "outflow_rate": outflow_rate,
        "last_updated": now.isoformat() + "Z",
    }
    cache_set(key, snapshot, ttl=30)
    return snapshot


def get_all_live_snapshots(db: Session) -> list[dict]:
    stations = db.query(Station).all()
    return [snap for s in stations if (snap := get_live_snapshot(db, s.id)) is not None]


def get_heatmap(db: Session) -> list[dict]:
    stations = db.query(Station).all()
    weekday = utcnow().weekday()

    # Load recent records once and bucket by (station, hour) in Python —
    # portable across SQLite/PostgreSQL (no dialect-specific datetime matching)
    # and avoids 240+ per-cell queries.
    cutoff = utcnow() - timedelta(days=45)
    recs = (
        db.query(RidershipRecord.station_id, RidershipRecord.timestamp, RidershipRecord.occupancy)
        .filter(RidershipRecord.timestamp >= cutoff)
        .order_by(RidershipRecord.timestamp.desc())
        .all()
    )
    occupancy_by_cell: dict[tuple[str, int], list[int]] = {}
    for station_id, ts, occ in recs:
        cell = occupancy_by_cell.setdefault((station_id, ts.hour), [])
        if len(cell) < _HEATMAP_SAMPLE_WINDOW:
            cell.append(occ)

    points: list[dict] = []
    for station in stations:
        for hour in range(24):
            samples = occupancy_by_cell.get((station.id, hour))
            if samples:
                avg_occ = sum(samples) / len(samples)
                pct = min(1.0, avg_occ / max(1, station.capacity_per_hour))
            else:
                pct = feat.station_baseline_occupancy_pct(hour)
                if weekday >= 5:
                    pct *= feat.WEEKEND_FACTOR
            points.append({
                "station_id": station.id,
                "station_name": station.name,
                "hour": hour,
                "occupancy_pct": round(pct * 100, 1),
                "congestion_level": compute_congestion_level(pct),
            })
    return points


def get_station_history(
    db: Session,
    station_id: str,
    hours: int = 24,
    start_at: datetime | None = None,
) -> list[dict]:
    """Gate entries/exits history for a station over `hours`.

    When `start_at` is provided it anchors the window at the selected date/time
    (`[start_at, start_at + hours)`), enabling historical date tracking. Without
    it the window is the last `hours` ending at now. Missing samples are filled
    with the baseline occupancy curve so charts never render empty.
    """
    now = utcnow()
    if start_at is not None:
        window_start = start_at
        window_end = start_at + timedelta(hours=hours)
        anchor_hour = start_at.hour
    else:
        window_start = now - timedelta(hours=hours)
        window_end = now
        anchor_hour = now.hour
    records = (
        db.query(RidershipRecord)
        .filter(
            RidershipRecord.station_id == station_id,
            RidershipRecord.timestamp >= window_start,
            RidershipRecord.timestamp < window_end,
        )
        .order_by(RidershipRecord.timestamp.asc())
        .all()
    )
    if not records:
        baseline = feat.station_baseline_occupancy_pct(anchor_hour)
        for i in range(hours):
            ts = window_start + timedelta(hours=i)
            records.append(RidershipRecord(
                station_id=station_id,
                timestamp=ts,
                entries=int(baseline * 400),
                exits=int(baseline * 400),
                occupancy=int(baseline * 300),
                congestion_level=compute_congestion_level(baseline),
            ))
    return [
        {
            "timestamp": r.timestamp.isoformat() + "Z",
            "entries": r.entries,
            "exits": r.exits,
            "occupancy": r.occupancy,
            "congestion_level": r.congestion_level,
        }
        for r in records
    ]


def ingest_crowd_record(
    db: Session,
    station_id: str,
    entries: int = 0,
    exits: int = 0,
    occupancy: int = 0,
    timestamp=None,
) -> dict:
    """Sensor/gate ingest: persists a ridership record, refreshes the live
    cache snapshot and returns the new live snapshot dict."""
    import uuid as _uuid

    station = db.query(Station).filter(Station.id == station_id).first()
    if not station:
        return None
    ts = timestamp or utcnow()
    # Derive congestion from occupancy vs capacity when not supplied.
    pct = min(1.2, max(0.0, occupancy / max(1, station.capacity_per_hour)))
    congestion = compute_congestion_level(pct)
    rec = RidershipRecord(
        id=f"RR-ING-{_uuid.uuid4().hex[:10]}",
        station_id=station_id,
        timestamp=ts,
        entries=int(entries),
        exits=int(exits),
        occupancy=int(occupancy),
        congestion_level=congestion,
    )
    db.add(rec)
    db.commit()
    # Invalidate cached snapshot so next read reflects the ingest.
    try:
        from app.core.cache import cache_set

        now = utcnow()
        occupancy_pct = round(min(1.0, occupancy / max(1, station.capacity_per_hour)) * 100, 1)
        snapshot = {
            "station_id": station.id,
            "station_name": station.name,
            "line": station.line,
            "occupancy": int(occupancy),
            "capacity": station.capacity_per_hour,
            "occupancy_pct": occupancy_pct,
            "congestion_level": congestion,
            "inflow_rate": round(int(entries) / 15.0, 1),
            "outflow_rate": round(int(exits) / 15.0, 1),
            "last_updated": now.isoformat() + "Z",
        }
        cache_set(f"crowd:latest:{station_id}", snapshot, ttl=30)
        log_sensor_event(snapshot)
        return snapshot
    except Exception:
        return get_live_snapshot(db, station_id)
