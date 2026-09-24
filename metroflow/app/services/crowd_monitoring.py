"""
Crowd Monitoring Module
- Passenger density tracking, congestion monitoring
- Heatmap generation
- Station-wise analytics, inflow/outflow analysis
Now uses REAL per-station capacity (app/data/station_capacity.csv) instead
of a flat number for every station.
"""
import pandas as pd

from app.data import repository as repo

CONGESTION_BANDS = [(0, 40, "Low"), (40, 70, "Moderate"), (70, 90, "High"), (90, 101, "Critical")]


def _band(pct: float) -> str:
    for low, high, label in CONGESTION_BANDS:
        if low <= pct < high:
            return label
    return "Critical"


def get_live_snapshot(on_date: str, hour: int) -> dict:
    stations = repo.all_stations_snapshot(on_date, hour)
    for s in stations:
        s["status"] = _band(s["congestion_pct"])
    return {
        "date": on_date,
        "hour": hour,
        "stations": stations,
        "system_total_entries": sum(s["entries"] for s in stations),
        "system_total_exits": sum(s["exits"] for s in stations),
        "critical_stations": [s["station"] for s in stations if s["status"] == "Critical"],
    }


def get_heatmap(on_date: str) -> dict:
    df = repo.load_data()
    day_df = df[df["Date"] == pd.to_datetime(on_date)]
    pivot = day_df.pivot_table(index="Station", columns="Hour", values="Entries", aggfunc="sum").fillna(0)
    congestion = pivot.astype(float).copy()
    for station in congestion.index:
        cap = repo.get_capacity(station)
        congestion.loc[station] = (pivot.loc[station] / cap * 100).clip(upper=100)
    congestion = congestion.round(1)
    return {
        "date": on_date,
        "stations": congestion.index.tolist(),
        "hours": congestion.columns.tolist(),
        "matrix": congestion.values.tolist(),
    }


def get_station_analytics(station: str, days: int = 30) -> dict:
    hist = repo.station_history(station, days=days)
    daily = hist.groupby(hist["Date"].dt.date)[["Entries", "Exits"]].sum()
    hourly = repo.hourly_profile(station)
    peak_hour = int(hourly.loc[hourly["Entries"].idxmax(), "Hour"])
    return {
        "station": station,
        "period_days": days,
        "capacity_per_hour": repo.get_capacity(station),
        "avg_daily_entries": round(daily["Entries"].mean(), 1),
        "avg_daily_exits": round(daily["Exits"].mean(), 1),
        "peak_hour": peak_hour,
        "hourly_profile": hourly.round(1).to_dict(orient="records"),
        "inflow_outflow_balance": round(daily["Entries"].mean() - daily["Exits"].mean(), 1),
    }


def get_system_congestion_ranking(on_date: str, hour: int) -> list[dict]:
    return get_live_snapshot(on_date, hour)["stations"]
