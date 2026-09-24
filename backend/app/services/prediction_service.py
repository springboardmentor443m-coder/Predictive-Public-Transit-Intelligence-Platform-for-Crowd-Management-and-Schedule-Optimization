from datetime import datetime, timedelta

from app.core.time import utcnow
from app.ml.model_wrappers import get_crowd_model, get_delay_model, get_demand_model
from app.services import scheduling_service


def _resolve_time(hour: int | None, weekday: int | None, scheduled_time: str | None) -> tuple[int, int, float]:
    now = utcnow()
    if hour is None:
        hour = now.hour
    if weekday is None:
        weekday = now.weekday()
    minutes = hour * 60 + 30
    if scheduled_time:
        hh_mm = scheduled_time.split(":")
        if len(hh_mm) >= 2:
            try:
                minutes = (int(hh_mm[0]) % 24) * 60 + int(hh_mm[1])
            except ValueError:
                pass
    return int(hour) % 24, int(weekday) % 7, float(minutes)


def predict_delay(req) -> dict:
    """NJ Transit ML delay forecast. If the delay artifacts are unavailable,
    raises RuntimeError (no synthetic fallback for delay models)."""
    hour, weekday, minutes = _resolve_time(req.hour, req.weekday, req.scheduled_time)
    return get_delay_model().predict(
        hour=hour,
        weekday=weekday,
        sched_minutes=minutes,
        stop_sequence=float(req.stop_sequence),
        line=req.line,
        from_station=req.from_station,
        to_station=req.to_station,
        train_type=req.train_type,
    )


def _station_ctx(db, station_id: str | None) -> dict | None:
    """Resolve a station row into the context dict used by the ML wrappers.
    Unknown/missing stations return None -> population-average forecast."""
    if not station_id:
        return None
    from app.models.station import Station

    s = db.query(Station).filter(Station.id == station_id).first()
    if s is None:
        return None
    return {"id": s.id, "capacity_per_hour": s.capacity_per_hour}


def predict_crowd(station_id: str | None = None, hours: int = 12, db=None) -> list[dict]:
    model = get_crowd_model()
    base_hour = utcnow().hour
    if db is None:
        from app.core.database import SessionLocal

        db = SessionLocal()
        try:
            return model.predict_hourly(base_hour, hours_ahead=hours, station=_station_ctx(db, station_id))
        finally:
            db.close()
    return model.predict_hourly(base_hour, hours_ahead=hours, station=_station_ctx(db, station_id))


def predict_crowd_at(
    start_at: datetime | None = None,
    station_id: str | None = None,
    hours: int = 12,
    db=None,
) -> list[dict]:
    """Forecast crowd occupancy for a user-selected date/time window. When
    `start_at` is omitted it defaults to the current hour (same as predict_crowd)."""
    if start_at is None:
        return predict_crowd(station_id, hours, db)
    model = get_crowd_model()
    if db is None:
        from app.core.database import SessionLocal

        db = SessionLocal()
        try:
            return model.predict_period(start_at, hours_ahead=hours, station=_station_ctx(db, station_id))
        finally:
            db.close()
    return model.predict_period(start_at, hours_ahead=hours, station=_station_ctx(db, station_id))


def forecast_demand(station_id: str | None = None, hours: int = 12, db=None) -> list[dict]:
    model = get_demand_model()
    base_hour = utcnow().hour
    if db is None:
        from app.core.database import SessionLocal

        db = SessionLocal()
        try:
            return model.forecast_hourly(base_hour, hours_ahead=hours, station=_station_ctx(db, station_id))
        finally:
            db.close()
    return model.forecast_hourly(base_hour, hours_ahead=hours, station=_station_ctx(db, station_id))


def forecast_demand_at(
    start_at: datetime | None = None,
    station_id: str | None = None,
    hours: int = 12,
    db=None,
) -> list[dict]:
    """Forecast gate demand for a user-selected date/time window."""
    if start_at is None:
        return forecast_demand(station_id, hours, db)
    model = get_demand_model()
    if db is None:
        from app.core.database import SessionLocal

        db = SessionLocal()
        try:
            return model.forecast_period(start_at, hours_ahead=hours, station=_station_ctx(db, station_id))
        finally:
            db.close()
    return model.forecast_period(start_at, hours_ahead=hours, station=_station_ctx(db, station_id))


def forecast_train(
    train_id: str,
    hours: int = 12,
    db=None,
    station_override_id: str | None = None,
) -> list[dict] | None:
    """Per-train forward forecast: for each upcoming scheduled stop, predict
    platform crowd occupancy + gate demand from the trained models. Returns a
    stop-level series for the next `hours` arrivals (None if train unknown)."""
    from app.models.schedule import TrainSchedule
    from app.models.station import Station
    from app.models.train import Train

    if db is None:
        from app.core.database import SessionLocal

        db = SessionLocal()
        close = True
    else:
        close = False

    try:
        train = db.query(Train).filter(Train.id == train_id).first()
        if train is None:
            return None
        now = utcnow()
        horizon = now + timedelta(hours=hours)
        stops = (
            db.query(TrainSchedule)
            .filter(
                TrainSchedule.train_id == train_id,
                TrainSchedule.arrival >= now,
                TrainSchedule.arrival <= horizon,
            )
            .order_by(TrainSchedule.arrival.asc())
            .all()
        )
        crowd_model = get_crowd_model()
        demand_model = get_demand_model()
        station_name = {s.id: s.name for s in db.query(Station).all()}

        results = []
        for stop in stops:
            ctx = {"id": stop.station_id, "capacity_per_hour": stop.station.capacity_per_hour}
            crowd = crowd_model.predict_period(stop.arrival, hours_ahead=1, station=_station_ctx(db, stop.station_id))
            demand = demand_model.forecast_period(stop.arrival, hours_ahead=1, station=_station_ctx(db, stop.station_id))
            cp = crowd[0] if crowd else {}
            dp = demand[0] if demand else {}
            results.append({
                "station_id": stop.station_id,
                "station_name": station_name.get(stop.station_id, stop.station_id),
                "direction": stop.direction,
                "arrival": stop.arrival.isoformat() + "Z",
                "headway_min": stop.headway_min,
                "status": stop.status,
                "delay_min": stop.delay_min or 0,
                "predicted_occupancy_pct": cp.get("predicted_occupancy_pct"),
                "congestion_level": cp.get("congestion_level"),
                "predicted_entries": dp.get("predicted_entries"),
                "predicted_exits": dp.get("predicted_exits"),
                "peak_probability": dp.get("peak_probability"),
            })
        return results
    finally:
        if close:
            db.close()


def smart_recommendations(db=None):
    if db is None:
        from app.core.database import SessionLocal

        db = SessionLocal()
        try:
            return scheduling_service.get_optimization_recommendations(db)
        finally:
            db.close()
    return scheduling_service.get_optimization_recommendations(db)


def traffic_patterns(db=None) -> list[dict]:
    """Traffic pattern analysis per PRD AI module: peak-hour detection and
    weekday/weekend profiling from historical ridership records."""
    if db is None:
        from app.core.database import SessionLocal
        from app.ml import features as feat

        db = SessionLocal()
        try:
            return _compute_patterns(db, feat)
        finally:
            db.close()
    from app.ml import features as feat
    return _compute_patterns(db, feat)


def _compute_patterns(db, feat) -> list[dict]:
    from app.models.ridership import RidershipRecord
    from app.models.station import Station

    stations = db.query(Station).all()
    results = []
    for s in stations:
        recs = (
            db.query(RidershipRecord)
            .filter(RidershipRecord.station_id == s.id)
            .order_by(RidershipRecord.timestamp.desc())
            .limit(24 * 7)
            .all()
        )
        hourly: dict[int, list[float]] = {h: [] for h in range(24)}
        weekday_vals: list[float] = []
        weekend_vals: list[float] = []
        for r in recs:
            occ_pct = r.occupancy / max(1, s.capacity_per_hour)
            hourly[r.timestamp.hour].append(occ_pct)
            if r.timestamp.weekday() >= 5:
                weekend_vals.append(occ_pct)
            else:
                weekday_vals.append(occ_pct)

        avg = {
            h: (sum(v) / len(v) if v else feat.BASELINE_OCCUPANCY[h])
            for h, v in hourly.items()
        }
        sorted_hours = sorted(avg, key=lambda h: avg[h], reverse=True)
        peak_hour = sorted_hours[0]
        weekend_factor = (
            round((sum(weekend_vals) / len(weekend_vals)) / max(1e-6, sum(weekday_vals) / len(weekday_vals)), 2)
            if weekend_vals and weekday_vals
            else feat.WEEKEND_FACTOR
        )

        results.append({
            "station_id": s.id,
            "station_name": s.name,
            "line": s.line,
            "peak_hour": peak_hour,
            "am_peak_hour": min(range(6, 12), key=lambda h: -avg[h]),
            "pm_peak_hour": min(range(16, 22), key=lambda h: -avg[h]),
            "peak_occupancy_pct": round(min(100.0, avg[peak_hour] * 100), 1),
            "weekend_factor": weekend_factor,
            "profile_24h": [round(avg[h] * 100, 1) for h in range(24)],
        })
    results.sort(key=lambda r: r["peak_occupancy_pct"], reverse=True)
    return results
