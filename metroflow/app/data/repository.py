"""
Data access layer: the only module that reads the CSV files.
Replace any of the three CSVs with a real download and nothing else changes.
"""
from functools import lru_cache
from pathlib import Path

import pandas as pd

DATA_DIR = Path(__file__).parent
RIDERSHIP_PATH = DATA_DIR / "taipei_mrt_2yr.csv"
CAPACITY_PATH = DATA_DIR / "station_capacity.csv"
DELAYS_PATH = DATA_DIR / "train_delays.csv"
FALLBACK_CAPACITY = 6000  # used only for a station missing from station_capacity.csv


@lru_cache(maxsize=1)
def load_data() -> pd.DataFrame:
    df = pd.read_csv(RIDERSHIP_PATH, parse_dates=["Date"])
    df["day_of_week"] = df["Date"].dt.dayofweek
    df["is_weekend"] = df["day_of_week"] >= 5
    df["month"] = df["Date"].dt.month
    df["net_flow"] = df["Entries"] - df["Exits"]
    return df


@lru_cache(maxsize=1)
def load_capacity() -> dict:
    df = pd.read_csv(CAPACITY_PATH)
    return dict(zip(df["Station"], df["HourlyCapacity"]))


@lru_cache(maxsize=1)
def load_delays() -> pd.DataFrame:
    return pd.read_csv(DELAYS_PATH, parse_dates=["Date"])


def get_capacity(station: str) -> int:
    return int(load_capacity().get(station, FALLBACK_CAPACITY))


def list_stations() -> list[str]:
    return sorted(load_data()["Station"].unique().tolist())


def latest_date() -> str:
    return str(load_data()["Date"].max().date())


def congestion_pct(entries: float, station: str) -> float:
    return round(min(100.0, entries / get_capacity(station) * 100), 1)


def station_snapshot(station: str, on_date: str, hour: int) -> dict:
    df = load_data()
    row = df[(df["Station"] == station) & (df["Date"] == pd.to_datetime(on_date)) & (df["Hour"] == hour)]
    if row.empty:
        return {}
    r = row.iloc[0]
    return {
        "station": station, "date": on_date, "hour": hour,
        "entries": int(r["Entries"]), "exits": int(r["Exits"]), "net_flow": int(r["net_flow"]),
        "capacity": get_capacity(station),
        "congestion_pct": congestion_pct(r["Entries"], station),
    }


def all_stations_snapshot(on_date: str, hour: int) -> list[dict]:
    df = load_data()
    subset = df[(df["Date"] == pd.to_datetime(on_date)) & (df["Hour"] == hour)]
    results = [
        {
            "station": r["Station"], "entries": int(r["Entries"]), "exits": int(r["Exits"]),
            "net_flow": int(r["net_flow"]), "capacity": get_capacity(r["Station"]),
            "congestion_pct": congestion_pct(r["Entries"], r["Station"]),
        }
        for _, r in subset.iterrows()
    ]
    return sorted(results, key=lambda x: -x["congestion_pct"])


def station_history(station: str, days: int = 30) -> pd.DataFrame:
    df = load_data()
    sub = df[df["Station"] == station].sort_values("Date")
    cutoff = sub["Date"].max() - pd.Timedelta(days=days)
    return sub[sub["Date"] > cutoff]


def hourly_profile(station: str) -> pd.DataFrame:
    sub = load_data()
    sub = sub[sub["Station"] == station]
    return sub.groupby("Hour")[["Entries", "Exits"]].mean().reset_index()


def station_delay_profile(station: str, days: int = 90) -> dict:
    delays = load_delays()
    sub = delays[delays["Station"] == station].sort_values("Date")
    empty = {
        "station": station, "period_days": days, "delay_events": 0, "avg_delay_minutes": 0.0,
        "max_delay_minutes": 0.0, "delay_frequency_pct": 0.0, "worst_delay_hour": None,
        "hourly_delay_profile": [],
    }
    if sub.empty:
        return empty
    recent = sub[sub["Date"] > sub["Date"].max() - pd.Timedelta(days=days)]
    if recent.empty:
        return empty
    hourly = recent.groupby("Hour")["DelayMinutes"].mean().reset_index()
    return {
        "station": station, "period_days": days,
        "delay_events": int(len(recent)),
        "avg_delay_minutes": round(float(recent["DelayMinutes"].mean()), 1),
        "max_delay_minutes": round(float(recent["DelayMinutes"].max()), 1),
        "delay_frequency_pct": round(len(recent) / (days * 24) * 100, 2),
        "worst_delay_hour": int(hourly.loc[hourly["DelayMinutes"].idxmax(), "Hour"]),
        "hourly_delay_profile": hourly.round(1).to_dict(orient="records"),
    }
