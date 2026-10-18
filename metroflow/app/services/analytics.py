"""
Analytics Dashboard Module: system traffic, station performance,
operational monitoring, heatmap report and AI insights.
"""
import pandas as pd

from app.data import repository as repo
from app.services import ai_prediction, crowd_monitoring


def system_traffic_report(days: int = 7) -> dict:
    df = repo.load_data()
    recent = df[df["Date"] > df["Date"].max() - pd.Timedelta(days=days)]
    by_station = recent.groupby("Station")[["Entries", "Exits"]].sum().sort_values("Entries", ascending=False)
    return {
        "period_days": days,
        "total_entries": int(recent["Entries"].sum()),
        "total_exits": int(recent["Exits"].sum()),
        "busiest_stations": by_station.head(5).reset_index().to_dict(orient="records"),
        "quietest_stations": by_station.tail(5).reset_index().to_dict(orient="records"),
    }


def station_performance_report(station: str, days: int = 30) -> dict:
    return {
        "station": station, "period_days": days,
        "crowd_analytics": crowd_monitoring.get_station_analytics(station, days=days),
        "delay_profile": repo.station_delay_profile(station, days=days),
        "ai_insights": ai_prediction.smart_recommendations(station, repo.latest_date()),
    }


def operational_monitoring_summary(on_date: str, hour: int) -> dict:
    snapshot = crowd_monitoring.get_live_snapshot(on_date, hour)
    delays = repo.load_delays()
    active = delays[(delays["Date"] == pd.to_datetime(on_date)) & (delays["Hour"] == hour)]
    return {
        "date": on_date, "hour": hour,
        "system_total_entries": snapshot["system_total_entries"],
        "system_total_exits": snapshot["system_total_exits"],
        "critical_station_count": len(snapshot["critical_stations"]),
        "critical_stations": snapshot["critical_stations"],
        "healthy_station_count": len(snapshot["stations"]) - len(snapshot["critical_stations"]),
        "active_delay_count": int(len(active)),
        "worst_active_delay_minutes": round(float(active["DelayMinutes"].max()), 1) if not active.empty else 0.0,
        "anomaly_count": len(ai_prediction.detect_anomalies(on_date, hour)["anomalies"]),
    }


def congestion_heatmap_report(on_date: str) -> dict:
    heatmap = crowd_monitoring.get_heatmap(on_date)
    worst = []
    for station, row in zip(heatmap["stations"], heatmap["matrix"]):
        top = max(row)
        worst.append({"station": station, "peak_congestion_pct": round(top, 1),
                      "peak_hour": heatmap["hours"][row.index(top)]})
    worst.sort(key=lambda x: -x["peak_congestion_pct"])
    return {**heatmap, "worst_congestion_points": worst[:5]}


def ai_insights_report(station: str, on_date: str) -> dict:
    return {
        "station": station, "date": on_date,
        "forecast": ai_prediction.forecast_peak_hours(station, on_date),
        "recommendations": ai_prediction.smart_recommendations(station, on_date),
        "model_metadata": ai_prediction.get_model_metadata(),
    }
