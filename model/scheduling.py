"""
scheduling.py (v3)
Per-station capacity-based crowd logic + alerts for MetroFlow.

Key change from earlier versions: crowd level is now a PERCENTAGE of
each station's own estimated capacity, not a fixed passenger-count
threshold shared across all stations (per mentor guidance - capacity
is "not constant").

Capacity estimation: 1.3x each station's historical peak passenger_count
in the real dataset. This is a documented assumption - official MTA
per-station capacity figures are not public. See build_capacity_table().
"""

import pandas as pd
import numpy as np

LOW_PCT = 0.50    # below this fraction of capacity -> "low"
HIGH_PCT = 0.80    # at/above this fraction of capacity -> "high" (mentor's reference point)


def build_capacity_table(df: pd.DataFrame) -> dict:
    """
    df must have columns: station, passenger_count
    Returns {station_name: capacity_int}

    Multiplier is 1.1x (not a huge buffer) so that a station's own
    historical peak hour realistically lands in the "high" band -
    which is the whole point of the alert. A too-generous buffer
    (e.g. 1.3x) would make "high" mathematically unreachable, since
    even the busiest hour ever recorded would fall under 80% of a
    padded capacity. Verified against the real dataset - see
    model/train_model_real.py evaluation notes.
    """
    cap = (df.groupby("station")["passenger_count"].max() * 1.1).round().astype(int)
    return cap.to_dict()


def crowd_percent(predicted_count: int, station: str, capacity_table: dict) -> float:
    capacity = capacity_table.get(station)
    if not capacity:
        return 0.0
    return round(100 * predicted_count / capacity, 1)


def crowd_level(pct: float) -> str:
    if pct >= HIGH_PCT * 100:
        return "high"
    elif pct >= LOW_PCT * 100:
        return "medium"
    else:
        return "low"


def recommendation(predicted_count: int, station: str, capacity_table: dict) -> dict:
    pct = crowd_percent(predicted_count, station, capacity_table)
    level = crowd_level(pct)

    if level == "high":
        message = (
            f"{station} is predicted at {pct}% of capacity "
            f"(~{predicted_count} passengers). Recommend increasing train "
            f"frequency and adding platform staff."
        )
    elif level == "medium":
        message = (
            f"{station} is predicted at {pct}% of capacity "
            f"(~{predicted_count} passengers). Current schedule should be "
            f"sufficient; monitor closer to the time."
        )
    else:
        message = (
            f"{station} is predicted at {pct}% of capacity "
            f"(~{predicted_count} passengers). No action needed."
        )

    return {
        "level": level,
        "crowd_pct": pct,
        "overcrowding_alert": level == "high",
        "message": message,
    }


# ---------------------------------------------------------------------------
# Simulated operational layers (arrivals, entry/exit, delay)
# All are documented, rule-based simulations - no real GPS/exit data exists
# publicly for this, per the project brief's own data-sources section.
# ---------------------------------------------------------------------------

def simulate_headway_minutes(hour: int) -> float:
    """Minutes between trains. Shorter at peak hours, longer off-peak."""
    if 8 <= hour <= 10 or 17 <= hour <= 19:
        return 3.5
    elif 11 <= hour <= 16:
        return 6.0
    else:
        return 9.0


def simulate_next_arrivals(hour: int, n: int = 3) -> list:
    """A short list of simulated upcoming arrival offsets in minutes."""
    headway = simulate_headway_minutes(hour)
    return [round(headway * (i + 1), 1) for i in range(n)]


def simulate_exit_estimate(entries_by_hour: dict, hour: int, offset_minutes: int = 22) -> int:
    """
    Estimate exits at `hour` as entries from ~offset_minutes earlier
    (rough proxy for average trip duration). entries_by_hour is a
    {hour: passenger_count} dict for a single station/day-type.
    Falls back to the current hour's entries if the offset hour is
    unavailable (e.g. at the start of service).
    """
    offset_hours = max(0, hour - round(offset_minutes / 60))
    return entries_by_hour.get(offset_hours, entries_by_hour.get(hour, 0))


def simulate_delay_minutes(crowd_pct: float, seed: int = None) -> float:
    """
    Delay increases as crowd % exceeds the high threshold, plus small
    random noise so it isn't perfectly deterministic. Derived from the
    real crowd prediction, not a disconnected random number.
    """
    rng = np.random.default_rng(seed)
    excess = max(0, crowd_pct - HIGH_PCT * 100)  # how far over 80% we are
    base_delay = excess * 0.15  # tuned so ~50% over capacity -> ~7.5 min delay
    noise = rng.normal(0, 0.8)
    return round(max(0, base_delay + noise), 1)


def delay_alert(delay_minutes: float, threshold: float = 4.0) -> bool:
    """Separate alert signal from overcrowding - fires on delay specifically."""
    return delay_minutes >= threshold
