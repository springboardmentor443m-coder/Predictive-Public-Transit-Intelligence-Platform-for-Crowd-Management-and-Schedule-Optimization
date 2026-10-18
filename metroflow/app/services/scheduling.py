"""
Scheduling Management: turns AI forecasts into train-frequency recommendations.
"""
from typing import Optional

from app.data import repository as repo
from app.services import ai_prediction
from app.services.crowd_monitoring import band

# Minutes between trains for each congestion band.
FREQUENCY_TABLE = {"Low": 10, "Moderate": 6, "High": 4, "Critical": 2.5}
DELAY_BACKLOG_MINUTES = 15  # a delay of this length doubles the required train frequency


def recommended_schedule(station: str, date: str) -> list[dict]:
    schedule = []
    for f in ai_prediction.forecast_peak_hours(station, date):
        b = band(f["predicted_congestion_pct"])
        schedule.append({
            "hour": f["hour"],
            "predicted_entries": f["predicted_entries"],
            "predicted_entries_90pct_range": f["predicted_entries_90pct_range"],
            "predicted_congestion_pct": f["predicted_congestion_pct"],
            "delay_probability": f["delay_probability"],
            "expected_delay_minutes": f["expected_delay_minutes"],
            "congestion_band": b,
            "recommended_frequency_min": FREQUENCY_TABLE[b],
        })
    return schedule


def peak_hour_summary(station: str, date: str) -> dict:
    schedule = recommended_schedule(station, date)
    peak = max(schedule, key=lambda x: x["predicted_congestion_pct"])
    return {
        "station": station, "date": date, "capacity": repo.get_capacity(station),
        "peak_hour": peak["hour"],
        "peak_congestion_pct": peak["predicted_congestion_pct"],
        "peak_predicted_entries": peak["predicted_entries"],
        "peak_delay_probability": peak["delay_probability"],
        "recommended_peak_frequency_min": peak["recommended_frequency_min"],
        "off_peak_hours": [s["hour"] for s in schedule if s["congestion_band"] == "Low"],
    }


def delay_report(station: str, days: int = 90) -> dict:
    return repo.station_delay_profile(station, days=days)


def adjust_frequency_for_delay(station: str, date: str, hour: int,
                               delay_minutes: Optional[float] = None) -> dict:
    """Delay-handling workflow.

    delay_minutes is the delay in progress (as reported by an operator). If omitted,
    the model's typical severity for a delay at this station/hour is used, giving a
    "what if a delay happens now" scenario. The train interval is tightened in
    proportion to the delay so the backlog does not compound into overcrowding.
    """
    base = recommended_schedule(station, date)[hour]
    scenario = delay_minutes is None
    if scenario:
        delay_minutes = ai_prediction.predict_delay(station, date, hour)["expected_severity_minutes_if_delayed"]
    factor = 1 + delay_minutes / DELAY_BACKLOG_MINUTES
    return {
        "station": station, "date": date, "hour": hour,
        "delay_minutes_used": round(float(delay_minutes), 1),
        "delay_source": "model scenario (typical severity if a delay occurs)" if scenario else "reported by operator",
        "original_recommended_frequency_min": base["recommended_frequency_min"],
        "adjusted_frequency_min": round(base["recommended_frequency_min"] / factor, 1),
        "note": "Interval tightened in proportion to the delay to absorb the backlog.",
    }
