"""
Alert & Notification Module (Week 5 -- start of Milestone 3)
- Overcrowding alerts (real per-station capacity, from live + AI-forecasted data)
- Delay notifications (from the real delay dataset / delay predictions)
- Emergency announcements
- Real-time updates feed (combined ticker for a dashboard)
"""
from datetime import datetime

import pandas as pd

from app.data import repository as repo
from app.services import ai_prediction, crowd_monitoring

OVERCROWD_THRESHOLD_PCT = 85
DELAY_ALERT_THRESHOLD_MIN = 7


def check_overcrowding_alerts(on_date: str, hour: int) -> list[dict]:
    """Live overcrowding alerts, using each station's real capacity."""
    snapshot = crowd_monitoring.get_live_snapshot(on_date, hour)
    alerts = []
    for s in snapshot["stations"]:
        if s["congestion_pct"] >= OVERCROWD_THRESHOLD_PCT:
            alerts.append({
                "type": "OVERCROWDING",
                "severity": "Critical" if s["congestion_pct"] >= 95 else "High",
                "station": s["station"],
                "congestion_pct": s["congestion_pct"],
                "capacity": s["capacity"],
                "message": (
                    f"Overcrowding at {s['station']}: {s['congestion_pct']}% of "
                    f"{s['capacity']}/hr capacity at {hour:02d}:00 on {on_date}."
                ),
                "generated_at": datetime.utcnow().isoformat(),
            })
    return alerts


def check_forecasted_overcrowding_alerts(station: str, on_date: str) -> list[dict]:
    """Forward-looking alerts using the AI demand forecast, not just live data --
    lets operators act before a station actually becomes critical."""
    forecast = ai_prediction.forecast_peak_hours(station, on_date)
    alerts = []
    for f in forecast:
        if f["predicted_congestion_pct"] >= OVERCROWD_THRESHOLD_PCT:
            alerts.append({
                "type": "FORECASTED_OVERCROWDING",
                "severity": "Critical" if f["predicted_congestion_pct"] >= 95 else "High",
                "station": station,
                "hour": f["hour"],
                "predicted_congestion_pct": f["predicted_congestion_pct"],
                "message": (
                    f"{station} forecast to hit {f['predicted_congestion_pct']}% capacity "
                    f"at {f['hour']:02d}:00 on {on_date}. Recommend pre-emptive frequency increase."
                ),
                "generated_at": datetime.utcnow().isoformat(),
            })
    return alerts


def check_delay_alerts(on_date: str, hour: int) -> list[dict]:
    """Delay notifications straight from the real (simulated) delay dataset."""
    delays = repo.load_delays()
    subset = delays[(delays["Date"] == pd.to_datetime(on_date)) & (delays["Hour"] == hour)]
    alerts = []
    for _, row in subset.iterrows():
        if row["DelayMinutes"] >= DELAY_ALERT_THRESHOLD_MIN:
            severity = "Critical" if row["DelayMinutes"] >= 15 else "High"
            alerts.append({
                "type": "DELAY",
                "severity": severity,
                "station": row["Station"],
                "delay_minutes": round(float(row["DelayMinutes"]), 1),
                "message": f"{round(float(row['DelayMinutes']), 1)} min delay reported near {row['Station']}.",
                "generated_at": datetime.utcnow().isoformat(),
            })
    return alerts


def create_emergency_announcement(station: str, message: str) -> dict:
    if station not in repo.list_stations():
        raise ValueError("Unknown station")
    return {
        "type": "EMERGENCY",
        "severity": "Critical",
        "station": station,
        "message": message,
        "generated_at": datetime.utcnow().isoformat(),
        "broadcast_channels": ["public_address", "mobile_push", "sms"],
    }


def real_time_feed(on_date: str, hour: int) -> dict:
    """Combined live ticker: overcrowding + delay alerts for the dashboard."""
    return {
        "date": on_date,
        "hour": hour,
        "overcrowding_alerts": check_overcrowding_alerts(on_date, hour),
        "delay_alerts": check_delay_alerts(on_date, hour),
        "refreshed_at": datetime.utcnow().isoformat(),
    }
