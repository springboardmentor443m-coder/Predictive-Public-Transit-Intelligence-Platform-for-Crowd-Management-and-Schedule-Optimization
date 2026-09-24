"""
Generates the ridership dataset in the official Taipei MRT schema
(Date, Hour, Station, Entries, Exits), PLUS two additions for Week 3-5:
  - a per-station capacity reference (station_capacity.csv)
  - a train delay log (train_delays.csv), correlated with congestion

Swap taipei_mrt_2yr.csv for the real download later -- station_capacity.csv
and train_delays.csv would then come from the transit authority's own
capacity/ops records, same schema.
"""
import numpy as np
import pandas as pd
from datetime import date, timedelta

RNG = np.random.default_rng(42)

# Real Taipei Metro stations, tagged with a relative ridership tier
STATIONS = {
    "Taipei Main Station": 5.0, "Zhongxiao Fuxing": 3.4, "Ximen": 3.0,
    "Banqiao": 2.8, "Taipei City Hall": 2.6, "Nanjing Fuxing": 2.2,
    "Guting": 2.0, "Dongmen": 1.8, "Da'an": 1.6, "Zhongshan": 1.6,
    "Shilin": 1.5, "Gongguan": 1.4, "Yongning": 1.3, "Nangang": 1.3,
    "Songshan Airport": 1.2, "Jiantan": 1.1, "Xindian": 1.1, "Muzha": 0.9,
    "Beitou": 0.8, "Tamsui": 0.9, "Xiaobitan": 0.4, "Yuanshan": 0.7,
    "Zhishan": 0.6, "Daqiaotou": 0.6, "Wanlong": 0.7, "Jingmei": 0.7,
    "Qizhang": 0.5, "Xindian District Office": 0.6,
    "Nangang Exhibition Center": 1.0, "Taipei Zoo": 0.5,
}
STATION_NAMES = list(STATIONS.keys())
STATION_WEIGHT = np.array(list(STATIONS.values()))

WEEKDAY_HOURLY_SHAPE = np.array([
    0.1, 0.05, 0.02, 0.02, 0.05, 0.3, 1.2, 3.2, 4.8, 3.0,
    2.0, 1.9, 2.1, 2.0, 1.9, 2.0, 2.4, 3.4, 4.6, 3.6,
    2.4, 1.6, 1.0, 0.4
])
WEEKEND_HOURLY_SHAPE = np.array([
    0.15, 0.08, 0.03, 0.02, 0.03, 0.1, 0.4, 0.9, 1.6, 2.4,
    2.9, 3.1, 3.2, 3.2, 3.1, 3.0, 2.9, 2.6, 2.3, 2.0,
    1.6, 1.1, 0.6, 0.25
])

BASE_ENTRIES_PER_UNIT = 380

# Real-world-informed per-station capacity: a station's platform/train
# throughput per hour scales with its role (interchange vs outer station),
# not a flat number for every station.
BASE_CAPACITY_PER_UNIT = 2400  # capacity units scale with the same tier weight as ridership


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


def generate_ridership(start: date = date(2022, 1, 1), end: date = date(2023, 12, 31),
                        out_path: str = "app/data/taipei_mrt_2yr.csv") -> pd.DataFrame:
    rows = []
    d = start
    while d <= end:
        is_weekend = d.weekday() >= 5
        shape = WEEKEND_HOURLY_SHAPE if is_weekend else WEEKDAY_HOURLY_SHAPE
        day_mult = _daily_multiplier(d)
        for hour in range(24):
            hour_mult = shape[hour]
            lam_entries = BASE_ENTRIES_PER_UNIT * STATION_WEIGHT * hour_mult * day_mult
            entries = RNG.poisson(np.clip(lam_entries, 0, None))
            lam_exits = lam_entries * RNG.uniform(0.90, 0.99, size=len(STATION_NAMES))
            exits = RNG.poisson(np.clip(lam_exits, 0, None))
            for name, e_in, e_out in zip(STATION_NAMES, entries, exits):
                rows.append((d.isoformat(), hour, name, int(e_in), int(e_out)))
        d += timedelta(days=1)

    df = pd.DataFrame(rows, columns=["Date", "Hour", "Station", "Entries", "Exits"])
    df.to_csv(out_path, index=False)
    return df


def generate_station_capacity(out_path: str = "app/data/station_capacity.csv") -> pd.DataFrame:
    """Per-station hourly throughput capacity, scaled by the same real-world
    tier used for ridership (interchange stations handle far more than outer
    stations)."""
    rows = []
    for name, weight in STATIONS.items():
        capacity = int(BASE_CAPACITY_PER_UNIT * weight)
        rows.append((name, capacity))
    df = pd.DataFrame(rows, columns=["Station", "HourlyCapacity"])
    df.to_csv(out_path, index=False)
    return df


def generate_delays(ridership_df: pd.DataFrame, out_path: str = "app/data/train_delays.csv") -> pd.DataFrame:
    """
    Simulated delay log correlated with congestion: busier station-hours
    have a higher probability and size of delay, matching the real-world
    pattern where overcrowding slows boarding/alighting and backs up the line.
    No real train GPS/delay feed exists in our current data source, so this
    is derived from ridership as the best available proxy.
    """
    df = ridership_df.copy()
    df["capacity"] = df["Station"].map(
        lambda s: int(BASE_CAPACITY_PER_UNIT * STATIONS[s])
    )
    df["congestion_ratio"] = (df["Entries"] / df["capacity"]).clip(upper=1.5)

    # Probability of a delay event this station-hour rises with congestion
    delay_prob = np.clip(0.03 + df["congestion_ratio"] * 0.25, 0, 0.6)
    has_delay = RNG.random(len(df)) < delay_prob

    delay_minutes = np.zeros(len(df))
    # delay magnitude also scales with congestion + random noise
    delay_minutes[has_delay] = RNG.gamma(
        shape=2.0, scale=2.0 + df.loc[has_delay, "congestion_ratio"].to_numpy() * 4, size=has_delay.sum()
    )
    df["DelayMinutes"] = delay_minutes.round(1)

    delays = df[df["DelayMinutes"] > 0][["Date", "Hour", "Station", "DelayMinutes"]]
    delays.to_csv(out_path, index=False)
    return delays


if __name__ == "__main__":
    ridership = generate_ridership()
    capacity = generate_station_capacity()
    delays = generate_delays(ridership)
    print(f"Ridership: {len(ridership):,} rows")
    print(f"Station capacity: {len(capacity)} stations")
    print(f"Delay events: {len(delays):,} rows ({len(delays) / len(ridership) * 100:.1f}% of station-hours)")
    print(capacity.sort_values('HourlyCapacity', ascending=False).head())
