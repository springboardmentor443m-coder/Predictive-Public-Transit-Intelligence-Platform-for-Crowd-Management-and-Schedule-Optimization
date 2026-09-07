import logging
import random
from datetime import datetime, timedelta

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
            "recorded_at": datetime.utcnow(),
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
    now = datetime.utcnow()
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
    return [get_live_snapshot(db, s.id) for s in stations if s]


def get_heatmap(db: Session) -> list[dict]:
    stations = db.query(Station).all()
    weekday = datetime.utcnow().weekday()

    # Load recent records once and bucket by (station, hour) in Python —
    # portable across SQLite/PostgreSQL (no dialect-specific datetime matching)
    # and avoids 240+ per-cell queries.
    cutoff = datetime.utcnow() - timedelta(days=45)
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


def get_station_history(db: Session, station_id: str, hours: int = 24) -> list[dict]:
    now = datetime.utcnow()
    since = now - timedelta(hours=hours)
    records = (
        db.query(RidershipRecord)
        .filter(RidershipRecord.station_id == station_id, RidershipRecord.timestamp >= since)
        .order_by(RidershipRecord.timestamp.asc())
        .all()
    )
    if not records:
        baseline = feat.station_baseline_occupancy_pct(now.hour)
        for i in range(hours):
            h = (now.hour - hours + i + 1) % 24
            records.append(RidershipRecord(
                station_id=station_id,
                timestamp=now - timedelta(hours=hours - i),
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
