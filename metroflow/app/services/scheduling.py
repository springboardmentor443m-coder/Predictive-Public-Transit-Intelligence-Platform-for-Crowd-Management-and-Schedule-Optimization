"""
Scheduling Management Module
- Train schedule management, peak-hour optimization, frequency adjustment
- Delay handling -- now driven by the real (simulated) delay dataset,
  not a manually-typed delay number.
"""
from app.data import repository as repo
from app.services import ai_prediction

FREQUENCY_TABLE = {"Low": 10, "Moderate": 6, "High": 4, "Critical": 2.5}


def _band(pct: float) -> str:
    if pct >= 90:
        return "Critical"
    if pct >= 70:
        return "High"
    if pct >= 40:
        return "Moderate"
    return "Low"


def recommended_schedule(station: str, date: str) -> list[dict]:
    demand = ai_prediction.forecast_peak_hours(station, date)
    delays = {d["hour"]: d["predicted_delay_minutes"] for d in ai_prediction.forecast_delays(station, date)}
    schedule = []
    for f in demand:
        band = _band(f["predicted_congestion_pct"])
        schedule.append({
            "hour": f["hour"],
            "predicted_congestion_pct": f["predicted_congestion_pct"],
            "predicted_delay_minutes": delays.get(f["hour"], 0),
            "congestion_band": band,
            "recommended_frequency_min": FREQUENCY_TABLE[band],
        })
    return schedule


def peak_hour_summary(station: str, date: str) -> dict:
    schedule = recommended_schedule(station, date)
    peak = max(schedule, key=lambda x: x["predicted_congestion_pct"])
    off_peak_hours = [s["hour"] for s in schedule if s["congestion_band"] == "Low"]
    return {
        "station": station, "date": date,
        "peak_hour": peak["hour"],
        "peak_congestion_pct": peak["predicted_congestion_pct"],
        "peak_expected_delay_minutes": peak["predicted_delay_minutes"],
        "recommended_peak_frequency_min": peak["recommended_frequency_min"],
        "off_peak_hours": off_peak_hours,
    }


def delay_report(station: str, days: int = 90) -> dict:
    """Real delay-pattern report for a station, from the delay dataset directly."""
    profile = repo.station_delay_profile(station, days=days)
    hourly = repo.hourly_delay_profile(station)
    worst_hour = int(hourly.loc[hourly["DelayMinutes"].idxmax(), "Hour"])
    return {
        **profile,
        "worst_delay_hour": worst_hour,
        "hourly_delay_profile": hourly.round(1).to_dict(orient="records"),
    }


def adjust_frequency_for_delay(station: str, date: str, hour: int) -> dict:
    """
    Delay-handling workflow: pulls the AI-predicted delay for this
    station/hour and tightens train frequency to absorb the backlog before
    it compounds into overcrowding.
    """
    delay_pred = ai_prediction.predict_delay(station, date, hour)
    demand_pred = ai_prediction.predict_demand(station, date, hour)
    band = _band(demand_pred["predicted_congestion_pct"])
    base_freq = FREQUENCY_TABLE[band]

    delay_minutes = delay_pred["predicted_delay_minutes"]
    backlog_factor = 1 + (delay_minutes / 30)
    adjusted_frequency = round(base_freq / backlog_factor, 1)

    return {
        "station": station, "date": date, "hour": hour,
        "predicted_delay_minutes": delay_minutes,
        "predicted_congestion_pct": demand_pred["predicted_congestion_pct"],
        "base_recommended_frequency_min": base_freq,
        "adjusted_frequency_min": adjusted_frequency,
        "note": "Frequency tightened to absorb delay-induced backlog before it compounds into overcrowding.",
    }
