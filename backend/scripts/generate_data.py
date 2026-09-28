import os
import sys
import time
from datetime import datetime, timedelta

import numpy as np
import pandas as pd

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from app.core.time import city_hour, city_weekday, hour_floor, local_instant, to_city, utcnow  # noqa: E402

_STARTED = time.time()


def _elapsed() -> float:
    return time.time() - _STARTED

rng = np.random.default_rng(42)

DATA_DIR = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "data")

STATIONS_CSV = os.path.join(DATA_DIR, "stations.csv")


def load_stations() -> list[tuple[str, str, str, int]]:
    """Station identity comes from data/stations.csv (real NYC MTA stations:
    authentic stop ids, names, trunk-route grouping, coordinates and
    service-frequency-derived capacities). Keeping it in one file stops the
    generators and the app from drifting apart."""
    df = pd.read_csv(STATIONS_CSV, dtype={"code": str})
    return [
        (str(r["code"]), str(r["name"]), str(r["line"]), int(r["capacity_per_hour"]))
        for _, r in df.iterrows()
    ]


def line_slug(line: str) -> str:
    """'N/Q/R/W' -> 'NQRW', used to build collision-free fleet codes."""
    return "".join(ch for ch in line.upper() if ch.isalnum())[:4] or "X"


STATIONS = load_stations()

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
    """Emit one row per UTC hour, labelled with the hour-of-day *as New York sees it*.

    The row is keyed on the UTC instant (so buckets are always exactly one hour
    apart and never collide across a DST shift), but `hour`, `weekday`,
    `is_weekend` and `is_peak` all describe the **local** time. Those are the
    columns the trainer feeds to the model, so labelling them locally is what
    makes "the 08:00 peak" mean 08:00 in New York rather than 08:00 UTC, which is
    04:00 local. Iterating UTC and *converting* (rather than iterating local
    hours) also means the spring-forward gap and the fall-back repeat are handled
    by the zone database instead of being papered over.
    """
    rows = []
    now = hour_floor(utcnow())
    # `start` MUST be midnight-aligned. Subtracting whole days from `now` keeps the
    # current hour-of-day on every row, so a row generated for the 07:00 peak got a
    # timestamp 17 hours later - the `hour` column then disagreed with
    # `timestamp.hour`, and the seeded 24h history showed the daily curve rotated
    # (overnight loads stamped 16:00) while contradicting the model forecasts.
    # DAYS-1 keeps the window ending *today* once `start` is floored to midnight.
    start = (now - timedelta(days=DAYS - 1)).replace(hour=0)
    for si, (code, name, line, cap) in enumerate(STATIONS):
        f = station_factor(si)
        for d in range(DAYS):
            day = start + timedelta(days=d)
            # The final day is partial so no row is dated in the future.
            hours = range(24) if d < DAYS - 1 else range(now.hour + 1)
            for utc_hour in hours:
                ts = day + timedelta(hours=utc_hour)
                hour = city_hour(ts)
                weekday = city_weekday(ts)
                weekend = weekday >= 5
                base = BASELINE[hour]
                if weekend:
                    base *= WEEKEND_FACTOR
                if hour in PEAK_HOURS and not weekend:
                    base *= 1.08
                noise = rng.normal(1.0, 0.07)
                occ_pct = float(np.clip(base * f * noise, 0.02, 1.15))
                # `occupancy` must satisfy occupancy / capacity == occ_pct, because
                # that ratio is how the API derives occupancy_pct (crowd_service)
                # and how the frontend colours every node. A divisor here made the
                # stored occupancy a quarter of the load the row's own
                # congestion_level described, so history read ~25% while being
                # labelled "critical".
                occupancy = int(cap * occ_pct)
                entries = int(occupancy * rng.uniform(0.85, 1.15))
                exits = int(entries * rng.uniform(0.75, 1.05))
                # Band the *stored integer* ratio, not the pre-truncation float.
                # The API recomputes occupancy_pct as occupancy/capacity and derives
                # its own level from that, so keying off occ_pct left a sliver of rows
                # whose stored level disagreed with the level the API returned for the
                # same row whenever int() truncation crossed a 55/75/90 boundary.
                stored_pct = occupancy / cap if cap else 0.0
                level = ("critical" if stored_pct >= 0.9 else "high" if stored_pct >= 0.75 else "medium" if stored_pct >= 0.55 else "low")
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
    # A departure timetable is a local-wall-clock artefact. Building the series
    # from `local_instant` (not `datetime(..., 5)`) is what keeps 05:00 meaning
    # 05:00 in New York, and keeps the delay-increase-at-peak test keyed on the
    # same local hours the rest of the app uses.
    start = local_instant((to_city(utcnow()) - timedelta(days=14)).date(), 5)
    for si, (code, name, line, cap) in enumerate(STATIONS):
        for t in range(trains_per_station):
            train_code = f"TR-{line_slug(line)}{si * trains_per_station + t + 1:02d}"
            for d in range(14):
                day = start + timedelta(days=d)
                dep = day + timedelta(minutes=int(rng.integers(0, 18) * 15))
                delay = max(0, int(rng.normal(2.5, 4.0)))
                if city_hour(dep) in PEAK_HOURS:
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
    print("Generating synthetic transportation datasets ...", flush=True)
    ridership = generate_ridership()
    ridership.to_csv(os.path.join(DATA_DIR, "ridership_hourly.csv"), index=False)
    print(f"  ridership_hourly.csv        {len(ridership):>7} rows", flush=True)

    ticketing = generate_ticketing_events(ridership)
    ticketing.to_csv(os.path.join(DATA_DIR, "ticketing_events.csv"), index=False)
    print(f"  ticketing_events.csv        {len(ticketing):>7} rows", flush=True)

    status = generate_train_status(ridership)
    status.to_csv(os.path.join(DATA_DIR, "train_status.csv"), index=False)
    print(f"  train_status.csv            {len(status):>7} rows", flush=True)

    # stations.csv is intentionally NOT rewritten: it is the curated real-world
    # source of truth for station identity, not generated output.
    print(f"  stations.csv (real, kept)   {len(STATIONS):>7} rows", flush=True)
    print(
        f"Done in {_elapsed():.1f}s -> {DATA_DIR} "
        f"(ridership {ridership['timestamp'].min()} .. {ridership['timestamp'].max()})",
        flush=True,
    )


if __name__ == "__main__":
    main()
