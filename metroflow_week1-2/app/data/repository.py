"""
Data access layer. Reads app/data/taipei_mrt_2yr.csv, which follows the
EXACT schema of the official dataset (Date, Hour, Station, Entries, Exits).
Swap that CSV for the real download and nothing else in the app needs to change.
"""
from functools import lru_cache
from pathlib import Path

import pandas as pd

DATA_PATH = Path(__file__).parent / "taipei_mrt_2yr.csv"

# Rough platform/train capacity assumption per station per hour, used to turn
# raw entries into a 0-100% congestion score. In production this would come
# from a station_capacity reference table.
DEFAULT_HOURLY_CAPACITY = 6000


@lru_cache(maxsize=1)
def load_data() -> pd.DataFrame:
    df = pd.read_csv(DATA_PATH, parse_dates=["Date"])
    df["day_of_week"] = df["Date"].dt.dayofweek  # 0=Mon
    df["is_weekend"] = df["day_of_week"] >= 5
    df["month"] = df["Date"].dt.month
    df["net_flow"] = df["Entries"] - df["Exits"]
    return df


def list_stations() -> list[str]:
    return sorted(load_data()["Station"].unique().tolist())


def latest_date() -> str:
    return str(load_data()["Date"].max().date())


def station_snapshot(station: str, on_date: str, hour: int) -> dict:
    df = load_data()
    row = df[
        (df["Station"] == station)
        & (df["Date"] == pd.to_datetime(on_date))
        & (df["Hour"] == hour)
    ]
    if row.empty:
        return {}
    r = row.iloc[0]
    congestion_pct = round(min(100, (r["Entries"] / DEFAULT_HOURLY_CAPACITY) * 100), 1)
    return {
        "station": station,
        "date": on_date,
        "hour": hour,
        "entries": int(r["Entries"]),
        "exits": int(r["Exits"]),
        "net_flow": int(r["net_flow"]),
        "congestion_pct": congestion_pct,
    }


def all_stations_snapshot(on_date: str, hour: int) -> list[dict]:
    df = load_data()
    subset = df[(df["Date"] == pd.to_datetime(on_date)) & (df["Hour"] == hour)]
    results = []
    for _, r in subset.iterrows():
        congestion_pct = round(min(100, (r["Entries"] / DEFAULT_HOURLY_CAPACITY) * 100), 1)
        results.append({
            "station": r["Station"],
            "entries": int(r["Entries"]),
            "exits": int(r["Exits"]),
            "net_flow": int(r["net_flow"]),
            "congestion_pct": congestion_pct,
        })
    return sorted(results, key=lambda x: -x["congestion_pct"])


def station_history(station: str, days: int = 30) -> pd.DataFrame:
    df = load_data()
    sub = df[df["Station"] == station].copy()
    sub = sub.sort_values("Date")
    cutoff = sub["Date"].max() - pd.Timedelta(days=days)
    return sub[sub["Date"] > cutoff]


def hourly_profile(station: str) -> pd.DataFrame:
    """Average entries/exits by hour of day for a station (for heatmaps/scheduling)."""
    df = load_data()
    sub = df[df["Station"] == station]
    return sub.groupby("Hour")[["Entries", "Exits"]].mean().reset_index()
