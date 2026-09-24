"""
Analytics Dashboard Module (Week 6 -- completes Milestone 3)
- Passenger traffic analytics (system-wide)
- Station performance reports (combines crowd + delay + AI insight)
- Operational monitoring (live system health summary)
- AI prediction insights + congestion heatmap reporting
"""
import pandas as pd

from app.data import repository as repo
from app.services import ai_prediction, crowd_monitoring


def system_traffic_report(days: int = 7) -> dict:
    """System-wide passenger traffic analytics over a recent window."""
    df = repo.load_data()
    cutoff = df["Date"].max() - pd.Timedelta(days=days)
    recent = df[df["Date"] > cutoff]

    by_station = (
        recent.groupby("Station")[["Entries", "Exits"]]
        .sum()
        .sort_values("Entries", ascending=False)
    )

    return {
        "period_days": days,
        "total_entries": int(recent["Entries"].sum()),
        "total_exits": int(recent["Exits"].sum()),
        "busiest_stations": by_station.head(5).reset_index().to_dict(orient="records"),
        "quietest_stations": by_station.tail(5).reset_index().to_dict(orient="records"),
    }


def station_performance_report(station: str, days: int = 30) -> dict:
    """Combines crowd analytics + delay profile + AI recommendations for one station --
    the single "how is this station doing" report."""
    crowd = crowd_monitoring.get_station_analytics(station, days=days)
    delay = repo.station_delay_profile(station, days=days)
    latest = repo.latest_date()
    ai_insights = ai_prediction.smart_recommendations(station, latest)

    return {
        "station": station,
        "period_days": days,
        "crowd_analytics": crowd,
        "delay_profile": delay,
        "ai_insights": ai_insights,
    }


def operational_monitoring_summary(on_date: str, hour: int) -> dict:
    """Live system health snapshot: how many stations are critical right now,
    and the system-wide entry/exit totals."""
    snapshot = crowd_monitoring.get_live_snapshot(on_date, hour)
    delays = repo.load_delays()
    active_delays = delays[(delays["Date"] == pd.to_datetime(on_date)) & (delays["Hour"] == hour)]

    return {
        "date": on_date,
        "hour": hour,
        "system_total_entries": snapshot["system_total_entries"],
        "system_total_exits": snapshot["system_total_exits"],
        "critical_station_count": len(snapshot["critical_stations"]),
        "critical_stations": snapshot["critical_stations"],
        "healthy_station_count": len(snapshot["stations"]) - len(snapshot["critical_stations"]),
        "active_delay_count": int(len(active_delays)),
        "worst_active_delay_minutes": (
            round(float(active_delays["DelayMinutes"].max()), 1) if not active_delays.empty else 0.0
        ),
    }


def congestion_heatmap_report(on_date: str) -> dict:
    """AI prediction insights + congestion heatmap reporting: the station x hour
    matrix plus a plain-language summary of the worst pockets of congestion."""
    heatmap = crowd_monitoring.get_heatmap(on_date)
    worst = []
    for station, row in zip(heatmap["stations"], heatmap["matrix"]):
        max_pct = max(row)
        worst_hour = heatmap["hours"][row.index(max_pct)]
        worst.append({"station": station, "peak_congestion_pct": round(max_pct, 1), "peak_hour": worst_hour})
    worst.sort(key=lambda x: -x["peak_congestion_pct"])

    return {
        "date": on_date,
        "stations": heatmap["stations"],
        "hours": heatmap["hours"],
        "matrix": heatmap["matrix"],
        "worst_congestion_points": worst[:5],
    }


def ai_insights_report(station: str, on_date: str) -> dict:
    """Standalone AI-prediction-insights section for the dashboard: forecasted
    demand/delay curve plus the smart recommendations derived from it."""
    return {
        "station": station,
        "date": on_date,
        "demand_forecast": ai_prediction.forecast_peak_hours(station, on_date),
        "delay_forecast": ai_prediction.forecast_delays(station, on_date),
        "recommendations": ai_prediction.smart_recommendations(station, on_date),
    }
