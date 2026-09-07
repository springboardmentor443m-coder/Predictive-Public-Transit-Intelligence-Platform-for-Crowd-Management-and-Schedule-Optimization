import os
from datetime import datetime, timedelta

import numpy as np
import pandas as pd

rng = np.random.default_rng(42)

DATA_DIR = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "data")

STATIONS = [
    ("ST01", "Central Junction", "Red", 520),
    ("ST02", "Riverside Park", "Red", 430),
    ("ST03", "Tech District", "Red", 610),
    ("ST04", "Old Town Market", "Blue", 480),
    ("ST05", "Stadium Plaza", "Blue", 700),
    ("ST06", "University Gate", "Blue", 560),
    ("ST07", "Airport Terminal", "Green", 540),
    ("ST08", "Harbor Front", "Green", 400),
    ("ST09", "North Industrial", "Green", 350),
    ("ST10", "South Commons", "Red", 450),
]

BASELINE = {
    0: 0.25, 1: 0.20, 2: 0.15, 3: 0.12, 4: 0.10, 5: 0.18,
    6: 0.30, 7: 0.85, 8: 1.00, 9: 0.75, 10: 0.55, 11: 0.50,
    12: 0.60, 13: 0.55, 14: 0.65, 15: 0.75, 16: 0.95, 17: 1.00,
    18: 0.90, 19: 0.75, 20: 0.60, 21: 0.50, 22: 0.40, 23: 0.35,
}

PEAK_HOURS = {7, 8, 9, 16, 17, 18}
WEEKEND_FACTOR = 0.72
DAYS = 60


def station_factor(idx: int) -> float:
    return 0.85 + 0.05 * ((idx * 37) % 7)


def generate_ridership() -> pd.DataFrame:
    rows = []
    start = datetime.utcnow().replace(minute=0, second=0, microsecond=0) - timedelta(days=DAYS)
    for si, (code, name, line, cap) in enumerate(STATIONS):
        f = station_factor(si)
        for d in range(DAYS):
            day = start + timedelta(days=d)
            weekday = day.weekday()
            weekend = weekday >= 5
            for hour in range(24):
                ts = day + timedelta(hours=hour)
                base = BASELINE[hour]
                if weekend:
                    base *= WEEKEND_FACTOR
                if hour in PEAK_HOURS and not weekend:
                    base *= 1.08
                noise = rng.normal(1.0, 0.07)
                occ_pct = float(np.clip(base * f * noise, 0.02, 1.15))
                entries = int(cap * occ_pct / 4 * rng.uniform(0.85, 1.15))
                exits = int(entries * rng.uniform(0.75, 1.05))
                occupancy = int(cap * occ_pct / 4)
                level = ("critical" if occ_pct >= 0.9 else "high" if occ_pct >= 0.75 else "medium" if occ_pct >= 0.55 else "low")
                rows.append({
                    "station_code": code,
                    "station_name": name,
                    "line": line,
                    "timestamp": ts,
                    "hour": hour,
                    "weekday": weekday,
                    "is_weekend": int(weekend),
                    "is_peak": int(hour in PEAK_HOURS),
                    "entries": entries,
                    "exits": exits,
                    "occupancy": occupancy,
                    "capacity": cap,
                    "occupancy_pct": round(occ_pct * 100, 2),
                    "congestion_level": level,
                })
    return pd.DataFrame(rows)


def generate_ticketing_events(ridership: pd.DataFrame, n: int = 50000) -> pd.DataFrame:
    sample = ridership.sample(n=min(n, len(ridership)), random_state=42).reset_index(drop=True)
    events = pd.DataFrame({
        "event_id": [f"TX{i:07d}" for i in range(len(sample))],
        "station_code": sample["station_code"],
        "timestamp": sample["timestamp"],
        "card_type": rng.choice(["smart_card", "single_ticket", "day_pass", "monthly_pass"], size=len(sample), p=[0.55, 0.2, 0.1, 0.15]),
        "direction": rng.choice(["entry", "exit"], size=len(sample)),
        "gate_id": [f"G{rng.integers(1, 13):02d}" for _ in range(len(sample))],
        "fare_amount": np.round(rng.uniform(1.5, 4.5, size=len(sample)), 2),
    })
    return events


def generate_train_status(ridership: pd.DataFrame) -> pd.DataFrame:
    rows = []
    trains_per_station = 3
    start = datetime.utcnow().replace(hour=5, minute=0, second=0, microsecond=0) - timedelta(days=14)
    for si, (code, name, line, cap) in enumerate(STATIONS):
        for t in range(trains_per_station):
            train_code = f"TR-{line[:1]}{si * 3 + t + 1:02d}"
            for d in range(14):
                day = start + timedelta(days=d)
                dep = day + timedelta(minutes=int(rng.integers(0, 18) * 15))
                delay = max(0, int(rng.normal(2.5, 4.0)))
                if dep.hour in PEAK_HOURS:
                    delay += int(rng.integers(0, 4))
                status = "on_time" if delay <= 2 else "minor_delay" if delay <= 6 else "delayed"
                rows.append({
                    "train_code": train_code,
                    "station_code": code,
                    "line": line,
                    "scheduled_departure": dep,
                    "actual_departure": dep + timedelta(minutes=delay),
                    "delay_min": delay,
                    "status": status,
                    "occupancy_pct": round(float(np.clip(rng.normal(0.68, 0.18), 0.05, 1.1)) * 100, 1),
                })
    return pd.DataFrame(rows)


def main() -> None:
    os.makedirs(DATA_DIR, exist_ok=True)
    print("Generating synthetic transportation datasets ...")
    ridership = generate_ridership()
    ridership.to_csv(os.path.join(DATA_DIR, "ridership_hourly.csv"), index=False)
    print(f"  ridership_hourly.csv        {len(ridership):>7} rows")

    ticketing = generate_ticketing_events(ridership)
    ticketing.to_csv(os.path.join(DATA_DIR, "ticketing_events.csv"), index=False)
    print(f"  ticketing_events.csv        {len(ticketing):>7} rows")

    status = generate_train_status(ridership)
    status.to_csv(os.path.join(DATA_DIR, "train_status.csv"), index=False)
    print(f"  train_status.csv            {len(status):>7} rows")

    stations_df = pd.DataFrame(STATIONS, columns=["code", "name", "line", "capacity_per_hour"])
    stations_df.to_csv(os.path.join(DATA_DIR, "stations.csv"), index=False)
    print(f"  stations.csv                {len(stations_df):>7} rows")
    print("Done ->", DATA_DIR)


if __name__ == "__main__":
    main()
