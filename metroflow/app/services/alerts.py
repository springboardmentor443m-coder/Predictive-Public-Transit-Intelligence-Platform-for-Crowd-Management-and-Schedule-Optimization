"""
Alert & Notification Module: live and forecast overcrowding, delays,
anomalies, emergency announcements and a combined real-time feed.
"""
from datetime import datetime, timezone

import pandas as pd

from app.data import repository as repo
from app.services import ai_prediction, crowd_monitoring

OVERCROWD_THRESHOLD_PCT = 85
DELAY_ALERT_THRESHOLD_MIN = 7


def _now() -> str:
    return datetime.now(timezone.utc).isoformat()


def check_overcrowding_alerts(on_date: str, hour: int) -> list[dict]:
    alerts = []
    for s in crowd_monitoring.get_live_snapshot(on_date, hour)["stations"]:
        if s["congestion_pct"] >= OVERCROWD_THRESHOLD_PCT:
            alerts.append({
                "type": "OVERCROWDING",
                "severity": "Critical" if s["congestion_pct"] >= 95 else "High",
                "station": s["station"], "congestion_pct": s["congestion_pct"], "capacity": s["capacity"],
                "message": (f"Overcrowding at {s['station']}: {s['congestion_pct']}% of "
                            f"{s['capacity']}/hr capacity at {hour:02d}:00 on {on_date}."),
                "generated_at": _now(),
            })
    return alerts


def check_forecasted_overcrowding_alerts(station: str, on_date: str) -> list[dict]:
    alerts = []
    for f in ai_prediction.forecast_peak_hours(station, on_date):
        if f["predicted_congestion_pct"] >= OVERCROWD_THRESHOLD_PCT:
            alerts.append({
                "type": "FORECASTED_OVERCROWDING",
                "severity": "Critical" if f["predicted_congestion_pct"] >= 95 else "High",
                "station": station, "hour": f["hour"], "predicted_congestion_pct": f["predicted_congestion_pct"],
                "message": (f"{station} forecast to reach {f['predicted_congestion_pct']}% capacity at "
                            f"{f['hour']:02d}:00 on {on_date}. Recommend a pre-emptive frequency increase."),
                "generated_at": _now(),
            })
    return alerts


def check_delay_alerts(on_date: str, hour: int) -> list[dict]:
    delays = repo.load_delays()
    subset = delays[(delays["Date"] == pd.to_datetime(on_date)) & (delays["Hour"] == hour)]
    alerts = []
    for _, row in subset.iterrows():
        minutes = round(float(row["DelayMinutes"]), 1)
        if minutes >= DELAY_ALERT_THRESHOLD_MIN:
            alerts.append({
                "type": "DELAY", "severity": "Critical" if minutes >= 15 else "High",
                "station": row["Station"], "delay_minutes": minutes,
                "message": f"{minutes} min delay reported near {row['Station']}.",
                "generated_at": _now(),
            })
    return alerts


def check_anomaly_alerts(on_date: str, hour: int) -> list[dict]:
    """Unusual passenger counts (spikes or drops) versus the AI forecast."""
    alerts = []
    for a in ai_prediction.detect_anomalies(on_date, hour)["anomalies"]:
        alerts.append({
            "type": "ANOMALY_" + a["verdict"],
            "severity": "High" if abs(a["z_score"]) >= 5 else "Moderate",
            "station": a["station"], "observed_entries": a["observed_entries"],
            "expected_entries": a["expected_entries"], "z_score": a["z_score"],
            "message": (f"{a['verdict'].title()} at {a['station']}: {a['observed_entries']:.0f} entries vs "
                        f"{a['expected_entries']:.0f} expected ({a['deviation_pct']:+.0f}%)."),
            "generated_at": _now(),
        })
    return alerts


def create_emergency_announcement(station: str, message: str) -> dict:
    if station not in repo.list_stations():
        raise ValueError("Unknown station")
    return {
        "type": "EMERGENCY", "severity": "Critical", "station": station, "message": message,
        "generated_at": _now(), "broadcast_channels": ["public_address", "mobile_push", "sms"],
    }


def real_time_feed(on_date: str, hour: int) -> dict:
    return {
        "date": on_date, "hour": hour,
        "overcrowding_alerts": check_overcrowding_alerts(on_date, hour),
        "delay_alerts": check_delay_alerts(on_date, hour),
        "anomaly_alerts": check_anomaly_alerts(on_date, hour),
        "refreshed_at": _now(),
    }
