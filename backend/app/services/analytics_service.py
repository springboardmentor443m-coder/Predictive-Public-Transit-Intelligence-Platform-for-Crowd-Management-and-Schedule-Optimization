import logging
from datetime import datetime, timedelta

from sqlalchemy import func
from sqlalchemy.orm import Session

from app.ml import features as feat
from app.models.alert import Alert
from app.models.ridership import RidershipRecord
from app.models.schedule import TrainSchedule
from app.models.station import Station
from app.models.train import Train
from app.services.crowd_service import get_all_live_snapshots

logger = logging.getLogger(__name__)

_PERF_SAMPLE_WINDOW = 48
_DEFAULT_TRAIN_CAPACITY = 1200


def _predicted_peak_hour(weekday: int) -> int:
    """Busiest expected hour today, from the baseline occupancy curve."""
    def expected_occupancy(h: int) -> float:
        occ = feat.BASELINE_OCCUPANCY[h]
        if weekday < 5:
            occ *= feat.PEAK_MULTIPLIER.get(h, 1.0)
        return occ

    return max(feat.BASELINE_OCCUPANCY.keys(), key=expected_occupancy)


def overview(db: Session) -> dict:
    now = datetime.utcnow()
    total_stations = db.query(Station).count()
    total_trains = db.query(Train).count()
    active_alerts = db.query(Alert).filter(Alert.is_acknowledged.is_(False)).count()

    snapshots = get_all_live_snapshots(db)
    if snapshots:
        current_occupancy = round(sum(s["occupancy_pct"] for s in snapshots) / len(snapshots), 1)
        avg_occupancy = current_occupancy
    else:
        current_occupancy = 0.0
        avg_occupancy = 0.0

    total_sched = db.query(TrainSchedule).count()
    on_time = db.query(TrainSchedule).filter(TrainSchedule.status == "on_time").count()
    on_time_pct = round((on_time / max(1, total_sched)) * 100, 1)

    delayed_count = db.query(TrainSchedule).filter(TrainSchedule.status == "delayed").count()
    peak_hour = _predicted_peak_hour(now.weekday())

    return {
        "total_stations": total_stations,
        "total_trains": total_trains,
        "active_alerts": active_alerts,
        "current_overall_occupancy_pct": current_occupancy,
        "avg_occupancy_pct": avg_occupancy,
        "on_time_pct": on_time_pct,
        "delayed_count": delayed_count,
        "predicted_peak_hour": peak_hour,
    }


def traffic_series(db: Session, hours: int = 24) -> list[dict]:
    now = datetime.utcnow()
    window_start = now - timedelta(hours=hours)
    rows = (
        db.query(TrainSchedule.train_id, TrainSchedule.arrival)
        .filter(TrainSchedule.arrival >= window_start)
        .all()
    )

    # One lookup for all train capacities instead of a lazy load per row.
    capacities = dict(db.query(Train.id, Train.capacity).all())

    buckets = [
        {"clock_hour": (window_start + timedelta(hours=i)).hour, "passenger_k": 0.0, "count": 0}
        for i in range(hours)
    ]
    for train_id, arrival in rows:
        idx = int((arrival - window_start).total_seconds() // 3600)
        if 0 <= idx < hours:
            buckets[idx]["count"] += 1
            buckets[idx]["passenger_k"] += (capacities.get(train_id) or _DEFAULT_TRAIN_CAPACITY) / 1000.0

    return [
        {
            "hour": b["clock_hour"],
            "passenger_k": round(b["passenger_k"], 2),
            "congestion_level": "low" if b["count"] < 5 else ("medium" if b["count"] < 10 else "high"),
        }
        for b in buckets
    ]


def station_performance(db: Session, limit: int = 15) -> list[dict]:
    stations = db.query(Station).all()

    # Latest `_PERF_SAMPLE_WINDOW` records per station, loaded once.
    rec_rows = (
        db.query(
            RidershipRecord.station_id,
            RidershipRecord.entries,
            RidershipRecord.exits,
            RidershipRecord.occupancy,
        )
        .order_by(RidershipRecord.timestamp.desc())
        .all()
    )
    latest_by_station: dict[str, list[tuple[int, int, int]]] = {}
    for station_id, entries, exits, occupancy in rec_rows:
        samples = latest_by_station.setdefault(station_id, [])
        if len(samples) < _PERF_SAMPLE_WINDOW:
            samples.append((entries, exits, occupancy))

    schedule_stats: dict[str, dict[str, int]] = {}
    for station_id, status, count in (
        db.query(TrainSchedule.station_id, TrainSchedule.status, func.count())
        .group_by(TrainSchedule.station_id, TrainSchedule.status)
        .all()
    ):
        stats = schedule_stats.setdefault(station_id, {"total": 0, "on_time": 0})
        stats["total"] += count
        if status == "on_time":
            stats["on_time"] += count

    perf = []
    for s in stations:
        capacity = max(1, s.capacity_per_hour)
        samples = latest_by_station.get(s.id) or []
        if samples:
            avg_occ = sum(r[2] for r in samples) / len(samples)
            peak_occ = max(r[2] for r in samples)
            entries_total = sum(r[0] for r in samples)
            exits_total = sum(r[1] for r in samples)
        else:
            avg_occ, peak_occ, entries_total, exits_total = 0, 0, 0, 0
        stats = schedule_stats.get(s.id, {"total": 0, "on_time": 0})
        punct = round(stats["on_time"] / max(1, stats["total"]) * 100, 1)
        perf.append({
            "station_id": s.id,
            "station_name": s.name,
            "avg_occupancy_pct": round(min(100, avg_occ / capacity * 100), 1),
            "peak_occupancy_pct": round(min(100, peak_occ / capacity * 100), 1),
            "congestion_score": round(min(100, avg_occ / capacity * 100), 1),
            "entries_total": entries_total,
            "exits_total": exits_total,
            "punctuality_pct": punct,
        })

    perf.sort(key=lambda x: x["congestion_score"], reverse=True)
    return perf[:limit]
