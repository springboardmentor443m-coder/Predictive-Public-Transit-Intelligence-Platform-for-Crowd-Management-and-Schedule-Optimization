"""
Generates three datasets that follow real open-data schemas, so the real files
can replace them later with zero code changes:

  taipei_mrt_2yr.csv     Date, Hour, Station, Entries, Exits
  station_capacity.csv   Station, HourlyCapacity
  train_delays.csv       Date, Hour, Station, DelayMinutes

Real schema reference: "Taipei MRT Station Entry and Exit Statistics"
(data.gov.tw, dataset 128683). The official file could not be downloaded from
the build environment, so this produces a realistic stand-in: real station
names, genuine rush-hour / weekend shape, seasonality, slow growth, holiday
dips, and delays that rise with congestion instead of being random noise.

Run from the project root:  python app/data/generate_dataset.py
"""
from datetime import date, timedelta
from pathlib import Path

import numpy as np
import pandas as pd

RNG = np.random.default_rng(42)
DATA_DIR = Path(__file__).parent

# Relative ridership weight per station, based on its real-world role.
STATIONS = {
    "Taipei Main Station": 5.0, "Zhongxiao Fuxing": 3.4, "Ximen": 3.0, "Banqiao": 2.8,
    "Taipei City Hall": 2.6, "Nanjing Fuxing": 2.2, "Guting": 2.0, "Dongmen": 1.8,
    "Da'an": 1.6, "Zhongshan": 1.6, "Shilin": 1.5, "Gongguan": 1.4, "Yongning": 1.3,
    "Nangang": 1.3, "Songshan Airport": 1.2, "Jiantan": 1.1, "Xindian": 1.1, "Muzha": 0.9,
    "Beitou": 0.8, "Tamsui": 0.9, "Xiaobitan": 0.4, "Yuanshan": 0.7, "Zhishan": 0.6,
    "Daqiaotou": 0.6, "Wanlong": 0.7, "Jingmei": 0.7, "Qizhang": 0.5,
    "Xindian District Office": 0.6, "Nangang Exhibition Center": 1.0, "Taipei Zoo": 0.5,
}
STATION_NAMES = list(STATIONS.keys())
STATION_WEIGHT = np.array(list(STATIONS.values()))

WEEKDAY_HOURLY_SHAPE = np.array([
    0.1, 0.05, 0.02, 0.02, 0.05, 0.3, 1.2, 3.2, 4.8, 3.0,
    2.0, 1.9, 2.1, 2.0, 1.9, 2.0, 2.4, 3.4, 4.6, 3.6,
    2.4, 1.6, 1.0, 0.4,
])
WEEKEND_HOURLY_SHAPE = np.array([
    0.15, 0.08, 0.03, 0.02, 0.03, 0.1, 0.4, 0.9, 1.6, 2.4,
    2.9, 3.1, 3.2, 3.2, 3.1, 3.0, 2.9, 2.6, 2.3, 2.0,
    1.6, 1.1, 0.6, 0.25,
])
BASE_ENTRIES_PER_UNIT = 380
CAPACITY_PER_UNIT = 2400  # passengers/hour per unit of station weight


def _daily_multiplier(d: date) -> float:
    day_of_year = d.timetuple().tm_yday
    seasonal = 1.0 + 0.08 * np.sin(2 * np.pi * (day_of_year - 60) / 365)
    growth = 1.0 + 0.00025 * (d - date(2022, 1, 1)).days
    holiday_dip = 1.0
    if d.month == 2 and 1 <= d.day <= 10:
        holiday_dip = 0.6
    if d.month == 10 and 8 <= d.day <= 10:
        holiday_dip = 0.75
    return seasonal * growth * holiday_dip


def generate_ridership(start=date(2022, 1, 1), end=date(2023, 12, 31)) -> pd.DataFrame:
    rows = []
    d = start
    while d <= end:
        shape = WEEKEND_HOURLY_SHAPE if d.weekday() >= 5 else WEEKDAY_HOURLY_SHAPE
        day_mult = _daily_multiplier(d)
        for hour in range(24):
            lam_entries = BASE_ENTRIES_PER_UNIT * STATION_WEIGHT * shape[hour] * day_mult
            entries = RNG.poisson(np.clip(lam_entries, 0, None))
            lam_exits = lam_entries * RNG.uniform(0.90, 0.99, size=len(STATION_NAMES))
            exits = RNG.poisson(np.clip(lam_exits, 0, None))
            for name, e_in, e_out in zip(STATION_NAMES, entries, exits):
                rows.append((d.isoformat(), hour, name, int(e_in), int(e_out)))
        d += timedelta(days=1)
    return pd.DataFrame(rows, columns=["Date", "Hour", "Station", "Entries", "Exits"])


def generate_capacity() -> pd.DataFrame:
    rows = [(name, int(round(CAPACITY_PER_UNIT * w, -1))) for name, w in STATIONS.items()]
    return pd.DataFrame(rows, columns=["Station", "HourlyCapacity"])


def generate_delays(ridership: pd.DataFrame, capacity: pd.DataFrame) -> pd.DataFrame:
    """Delay events whose frequency and severity rise with congestion."""
    cap_map = dict(zip(capacity["Station"], capacity["HourlyCapacity"]))
    df = ridership.copy()
    df["congestion_pct"] = (df["Entries"] / df["Station"].map(cap_map) * 100).clip(upper=100)
    delay_prob = 0.01 + (df["congestion_pct"] / 100) * 0.04
    delayed = df[RNG.random(len(df)) < delay_prob].copy()
    severity = 2 + (delayed["congestion_pct"] / 100) * 15 + RNG.exponential(3, size=len(delayed))
    delayed["DelayMinutes"] = np.round(np.clip(severity, 1, 35), 1)
    return delayed[["Date", "Hour", "Station", "DelayMinutes"]].reset_index(drop=True)


if __name__ == "__main__":
    ridership = generate_ridership()
    capacity = generate_capacity()
    delays = generate_delays(ridership, capacity)
    ridership.to_csv(DATA_DIR / "taipei_mrt_2yr.csv", index=False)
    capacity.to_csv(DATA_DIR / "station_capacity.csv", index=False)
    delays.to_csv(DATA_DIR / "train_delays.csv", index=False)
    print(f"Ridership: {len(ridership):,} rows, {ridership['Station'].nunique()} stations")
    print(f"Capacity:  {len(capacity)} stations")
    print(f"Delays:    {len(delays):,} events ({len(delays) / len(ridership) * 100:.2f}% of station-hours)")
