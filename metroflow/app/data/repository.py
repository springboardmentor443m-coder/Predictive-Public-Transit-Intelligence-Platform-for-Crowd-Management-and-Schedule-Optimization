"""
Data access layer. Reads three files, all matching real-world open-data
schemas so any of them can be swapped for the genuine official version later:
  - taipei_mrt_2yr.csv    -> Date, Hour, Station, Entries, Exits
  - station_capacity.csv  -> Station, HourlyCapacity   (fixes the old flat-6000 placeholder)
  - train_delays.csv      -> Date, Hour, Station, DelayMinutes
"""
from functools import lru_cache
from pathlib import Path

import pandas as pd

DATA_DIR = Path(__file__).parent
RIDERSHIP_PATH = DATA_DIR / "taipei_mrt_2yr.csv"
CAPACITY_PATH = DATA_DIR / "station_capacity.csv"
DELAYS_PATH = DATA_DIR / "train_delays.csv"


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
    """Station -> hourly capacity. Replaces the old flat DEFAULT_HOURLY_CAPACITY."""
    df = pd.read_csv(CAPACITY_PATH)
    return dict(zip(df["Station"], df["HourlyCapacity"]))


@lru_cache(maxsize=1)
def load_delays() -> pd.DataFrame:
    return pd.read_csv(DELAYS_PATH, parse_dates=["Date"])


def get_capacity(station: str) -> int:
    caps = load_capacity()
    return caps.get(station, 6000)  # fallback only if a station is missing from the table


def list_stations() -> list[str]:
    return sorted(load_data()["Station"].unique().tolist())


def latest_date() -> str:
    return str(load_data()["Date"].max().date())


def _congestion_pct(entries: float, station: str) -> float:
    cap = get_capacity(station)
    return round(min(100, (entries / cap) * 100), 1)


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
    return {
        "station": station,
        "date": on_date,
        "hour": hour,
        "entries": int(r["Entries"]),
        "exits": int(r["Exits"]),
        "net_flow": int(r["net_flow"]),
        "capacity": get_capacity(station),
        "congestion_pct": _congestion_pct(r["Entries"], station),
    }


def all_stations_snapshot(on_date: str, hour: int) -> list[dict]:
    df = load_data()
    subset = df[(df["Date"] == pd.to_datetime(on_date)) & (df["Hour"] == hour)]
    results = []
    for _, r in subset.iterrows():
        results.append({
            "station": r["Station"],
            "entries": int(r["Entries"]),
            "exits": int(r["Exits"]),
            "net_flow": int(r["net_flow"]),
            "capacity": get_capacity(r["Station"]),
            "congestion_pct": _congestion_pct(r["Entries"], r["Station"]),
        })
    return sorted(results, key=lambda x: -x["congestion_pct"])


def station_history(station: str, days: int = 30) -> pd.DataFrame:
    df = load_data()
    sub = df[df["Station"] == station].copy()
    sub = sub.sort_values("Date")
    cutoff = sub["Date"].max() - pd.Timedelta(days=days)
    return sub[sub["Date"] > cutoff]


def hourly_profile(station: str) -> pd.DataFrame:
    df = load_data()
    sub = df[df["Station"] == station]
    return sub.groupby("Hour")[["Entries", "Exits"]].mean().reset_index()


def station_delay_profile(station: str, days: int = 90) -> dict:
    """Average delay minutes and delay frequency for a station, recent window."""
    delays = load_delays()
    sub = delays[delays["Station"] == station]
    cutoff = sub["Date"].max() - pd.Timedelta(days=days) if not sub.empty else None
    if cutoff is not None:
        sub = sub[sub["Date"] > cutoff]

    total_hours = load_data()[load_data()["Station"] == station].shape[0]
    return {
        "station": station,
        "period_days": days,
        "delay_events": int(len(sub)),
        "avg_delay_minutes": round(sub["DelayMinutes"].mean(), 1) if not sub.empty else 0.0,
        "max_delay_minutes": round(sub["DelayMinutes"].max(), 1) if not sub.empty else 0.0,
        "delay_frequency_pct": round(len(sub) / total_hours * 100, 2) if total_hours else 0.0,
    }


def hourly_delay_profile(station: str) -> pd.DataFrame:
    """Average delay by hour of day for a station -- feeds scheduling recommendations."""
    delays = load_delays()
    sub = delays[delays["Station"] == station]
    if sub.empty:
        return pd.DataFrame({"Hour": range(24), "DelayMinutes": [0.0] * 24})
    profile = sub.groupby("Hour")["DelayMinutes"].mean().reindex(range(24), fill_value=0.0)
    return profile.reset_index()
