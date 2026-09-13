from datetime import datetime

import numpy as np


HOURS_PER_DAY = 24

BASELINE_OCCUPANCY = {
    6: 0.30, 7: 0.85, 8: 1.00, 9: 0.75, 10: 0.55, 11: 0.50,
    12: 0.60, 13: 0.55, 14: 0.65, 15: 0.75, 16: 0.95, 17: 1.00,
    18: 0.90, 19: 0.75, 20: 0.60, 21: 0.50, 22: 0.40, 23: 0.35,
    0: 0.25, 1: 0.20, 2: 0.15, 3: 0.12, 4: 0.10, 5: 0.18,
}

PEAK_MULTIPLIER = {
    7: 1.05, 8: 1.10, 9: 1.02, 16: 1.08, 17: 1.12, 18: 1.05,
}

WEEKEND_FACTOR = 0.72

# Canonical station order — must match scripts/generate_data.py STATIONS.
# Stored inside trained artifacts so inference uses the exact same encoding.
STATION_LIST = [
    "ST01", "ST02", "ST03", "ST04", "ST05",
    "ST06", "ST07", "ST08", "ST09", "ST10",
]
MAX_CAPACITY = 700.0


def hour_to_features(hour: int, weekday: int) -> np.ndarray:
    is_weekend = 1.0 if weekday >= 5 else 0.0
    is_peak = 1.0 if hour in PEAK_MULTIPLIER else 0.0
    hour_sin = np.sin(2 * np.pi * hour / HOURS_PER_DAY)
    hour_cos = np.cos(2 * np.pi * hour / HOURS_PER_DAY)
    dow_sin = np.sin(2 * np.pi * weekday / 7)
    dow_cos = np.cos(2 * np.pi * weekday / 7)
    return np.array([hour_sin, hour_cos, is_peak, is_weekend, dow_sin, dow_cos, is_weekend * is_peak])


def station_to_features(station_id: str | None, capacity_per_hour: float | None) -> np.ndarray:
    """One-hot station identity + normalized capacity. Unknown stations encode
    as all-zeros (population-average behaviour)."""
    one_hot = np.zeros(len(STATION_LIST))
    if station_id and station_id in STATION_LIST:
        one_hot[STATION_LIST.index(station_id)] = 1.0
    cap_norm = np.array([min(1.5, (capacity_per_hour or 520.0) / MAX_CAPACITY)])
    return np.concatenate([one_hot, cap_norm])


def row_features(hour: int, weekday: int, station_id: str | None = None, capacity_per_hour: float | None = None) -> np.ndarray:
    return np.concatenate([hour_to_features(hour, weekday), station_to_features(station_id, capacity_per_hour)])


def kaggle_row_features(
    hour: int,
    weekday: int,
    station_code: str | None,
    capacity_per_hour: float | None,
    stations: list[str],
    cap_norm_scale: float,
) -> np.ndarray:
    """Build one inference row in the Kaggle training schema:
    [7 temporal][one-hot over the artifact's station codes][capacity_norm]."""
    temporal = hour_to_features(hour, weekday)
    one_hot = np.zeros(len(stations))
    if station_code and station_code in stations:
        one_hot[stations.index(station_code)] = 1.0
    cap_norm = np.array([min(1.5, max(0.0, (capacity_per_hour or 0.0) / max(1e-9, cap_norm_scale)))])
    return np.concatenate([temporal, one_hot, cap_norm])


def station_baseline_occupancy_pct(hour: int) -> float:
    return BASELINE_OCCUPANCY[hour]


def demand_base_entries(hour: int) -> float:
    return BASELINE_OCCUPANCY[hour] * 1200


def feature_matrix_for_station(station_id: str, hours: list[int], weekday: int) -> np.ndarray:
    rows = [hour_to_features(h, weekday) for h in hours]
    return np.array(rows)


def congestion_from_pct(pct: float) -> str:
    if pct >= 0.90:
        return "critical"
    if pct >= 0.75:
        return "high"
    if pct >= 0.55:
        return "medium"
    return "low"


__all__ = [
    "HOURS_PER_DAY",
    "BASELINE_OCCUPANCY",
    "PEAK_MULTIPLIER",
    "WEEKEND_FACTOR",
    "STATION_LIST",
    "hour_to_features",
    "station_to_features",
    "row_features",
    "kaggle_row_features",
    "station_baseline_occupancy_pct",
    "demand_base_entries",
    "feature_matrix_for_station",
    "congestion_from_pct",
]
