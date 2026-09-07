from datetime import datetime

from app.ml.model_wrappers import get_crowd_model, get_demand_model
from app.services import scheduling_service


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
    base_hour = datetime.utcnow().hour
    if db is None:
        from app.core.database import SessionLocal

        db = SessionLocal()
        try:
            return model.predict_hourly(base_hour, hours_ahead=hours, station=_station_ctx(db, station_id))
        finally:
            db.close()
    return model.predict_hourly(base_hour, hours_ahead=hours, station=_station_ctx(db, station_id))


def forecast_demand(station_id: str | None = None, hours: int = 12, db=None) -> list[dict]:
    model = get_demand_model()
    base_hour = datetime.utcnow().hour
    if db is None:
        from app.core.database import SessionLocal

        db = SessionLocal()
        try:
            return model.forecast_hourly(base_hour, hours_ahead=hours, station=_station_ctx(db, station_id))
        finally:
            db.close()
    return model.forecast_hourly(base_hour, hours_ahead=hours, station=_station_ctx(db, station_id))


def smart_recommendations(db=None):
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
        am_peak = min(sorted_hours[:12], key=lambda h: -avg[h]) if recs else 8
        pm_peak = min(sorted_hours[12:], key=lambda h: -avg[h]) if recs else 17
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
