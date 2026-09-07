import logging
from datetime import datetime, timedelta

from sqlalchemy.orm import Session

from app.models.schedule import TrainSchedule
from app.models.station import Station
from app.models.train import Train
from app.schemas.prediction import Recommendation
from app.ml import features as feat
from app.services import prediction_service

logger = logging.getLogger(__name__)

TRAIN_CAPACITY_DEFAULT = 1200
PLATFORMS_PER_STATION = 4
TARGET_OCCUPANCY_PCT = 0.82


def compute_recommended_headway(demand_entries: int, train_capacity: int = TRAIN_CAPACITY_DEFAULT) -> int:
    """Recommended headway in minutes for an hourly demand level.

    `demand_entries` is passengers/hour and `train_capacity` is passengers
    per train — do not substitute hourly platform throughput for it.
    """
    needed_trains = max(1, round(demand_entries / (train_capacity * 0.85)))
    headway_min = min(15, max(3, round(120 / needed_trains)))
    return headway_min


def get_optimization_recommendations(db: Session) -> list[dict]:
    now = datetime.utcnow()
    weekday = now.weekday()
    recommendations = []
    stations = db.query(Station).all()
    base_hour = now.hour
    for station in stations:
        schedule_row = (
            db.query(TrainSchedule)
            .filter(
                TrainSchedule.station_id == station.id,
                TrainSchedule.arrival >= now - timedelta(hours=1),
                TrainSchedule.arrival <= now + timedelta(hours=1),
            )
            .first()
        )
        current_headway = schedule_row.headway_min if schedule_row else 6
        peak_prob = feat.PEAK_MULTIPLIER.get(base_hour, 1.0) if weekday < 5 else 1.0
        baseline_entries = int(feat.demand_base_entries(base_hour) * (1.15 if base_hour in feat.PEAK_MULTIPLIER else 1.0) * (1.0 if weekday < 5 else feat.WEEKEND_FACTOR))
        recommended_headway = compute_recommended_headway(baseline_entries, TRAIN_CAPACITY_DEFAULT)

        utilization = round(baseline_entries / max(1, station.capacity_per_hour) * 100, 1)
        reason = (
            "Peak-hour demand elevated; reduced headway recommended"
            if base_hour in feat.PEAK_MULTIPLIER
            else "Steady demand; standard headway sufficient"
        )
        recommendations.append({
            "station_id": station.id,
            "station_name": station.name,
            "current_headway_min": current_headway,
            "recommended_headway_min": recommended_headway,
            "reason": reason,
            "capacity_utilization_pct": utilization,
        })
    return recommendations


def handle_delay(db: Session, schedule_id: str, delay_min: int) -> dict:
    schedule = db.query(TrainSchedule).filter(TrainSchedule.id == schedule_id).first()
    if not schedule:
        from fastapi import HTTPException
        raise HTTPException(status_code=404, detail="Schedule not found")
    schedule.delay_min = delay_min
    schedule.status = "delayed" if delay_min > 2 else "on_time"
    db.add(schedule)
    db.commit()
    db.refresh(schedule)

    following = (
        db.query(TrainSchedule)
        .filter(
            TrainSchedule.train_id == schedule.train_id,
            TrainSchedule.station_id == schedule.station_id,
            TrainSchedule.arrival > schedule.arrival,
            TrainSchedule.direction == schedule.direction,
        )
        .order_by(TrainSchedule.arrival.asc())
        .first()
    )
    recovered = False
    if following and delay_min > 5:
        following.arrival = following.arrival + timedelta(minutes=delay_min)
        following.departure = following.departure + timedelta(minutes=delay_min)
        db.add(following)
        db.commit()
        db.refresh(following)
        recovered = True

    alert_id = None
    if delay_min >= 3:
        from app.services.alert_service import raise_delay_alert

        alert = raise_delay_alert(db, schedule, delay_min)
        alert_id = alert.id

    return {
        "schedule_id": schedule.id,
        "status": schedule.status,
        "delay_min": schedule.delay_min,
        "recovery_action": "propagated_delay_to_following_train" if recovered else "recovered_within_tolerance",
        "alert_id": alert_id,
    }


def apply_headway(db: Session, station_id: str, headway_min: int | None = None) -> dict:
    """Applies a frequency adjustment to all future schedules at a station.

    Uses the AI-recommended headway when none is provided (PRD: frequency adjustment).
    """
    from fastapi import HTTPException

    station = db.query(Station).filter(Station.id == station_id).first()
    if not station:
        raise HTTPException(status_code=404, detail="Station not found")

    target = headway_min
    source = "manual"
    if target is None:
        recs = get_optimization_recommendations(db)
        rec = next((r for r in recs if r["station_id"] == station_id), None)
        if not rec:
            raise HTTPException(status_code=404, detail="No recommendation available for station")
        target = rec["recommended_headway_min"]
        source = "ai_recommendation"

    target = max(2, min(30, int(target)))
    now = datetime.utcnow()
    rows = (
        db.query(TrainSchedule)
        .filter(TrainSchedule.station_id == station_id, TrainSchedule.arrival >= now)
        .all()
    )
    for row in rows:
        row.headway_min = target
        row.is_peak = "yes" if target <= 6 else "no"
        db.add(row)
    db.commit()

    logger.info(f"Applied headway {target}min at {station.name} ({len(rows)} schedules, {source})")
    return {
        "station_id": station_id,
        "station_name": station.name,
        "applied_headway_min": target,
        "source": source,
        "schedules_updated": len(rows),
    }


def list_schedules(db: Session, limit: int = 100):
    return (
        db.query(TrainSchedule)
        .order_by(TrainSchedule.arrival.desc())
        .limit(limit)
        .all()
    )
