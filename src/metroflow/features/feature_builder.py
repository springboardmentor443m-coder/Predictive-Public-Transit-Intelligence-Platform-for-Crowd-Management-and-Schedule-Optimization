"""Feature engineering on top of the station-hourly aggregated table.

Target: next-hour station inflow (t+1), per the Step 1 ML problem definition.
Only features derivable from the raw dataset's own date/hour/station/count
columns are built here — no fabricated capacity, GPS, or sensor signals.
"""
from __future__ import annotations

import sys
from pathlib import Path

import numpy as np
import pandas as pd

sys.path.append(str(Path(__file__).resolve().parents[3]))
from config.settings import (
    PREDICTION_HORIZON_HOURS,
    TARGET_DATETIME_COL,
    TARGET_INFLOW_COL,
    TARGET_OUTFLOW_COL,
    TARGET_STATION_COL,
)

LAG_HOURS = [1, 2, 3, 24, 168]  # t-1h, t-2h, t-3h, same hour yesterday, same hour last week
ROLLING_WINDOWS = [24, 168]  # 1-day and 1-week rolling means
TARGET_COLUMN = "target_inflow_next_hour"


def add_calendar_features(df: pd.DataFrame) -> pd.DataFrame:
    df = df.copy()
    dt = df[TARGET_DATETIME_COL]
    df["hour_of_day"] = dt.dt.hour
    df["day_of_week"] = dt.dt.dayofweek
    df["is_weekend"] = df["day_of_week"].isin([5, 6]).astype(int)
    df["month"] = dt.dt.month
    df["is_morning_peak"] = df["hour_of_day"].isin([7, 8, 9]).astype(int)
    df["is_evening_peak"] = df["hour_of_day"].isin([17, 18, 19]).astype(int)
    return df


def add_lag_and_rolling_features(df: pd.DataFrame) -> pd.DataFrame:
    """Add lag and rolling-mean features per station, computed on a complete
    (station, hourly) time index so gaps in the raw data don't leak future
    values backward into lags.
    """
    df = df.sort_values([TARGET_STATION_COL, TARGET_DATETIME_COL]).copy()

    reindexed_parts = []
    for station, group in df.groupby(TARGET_STATION_COL, sort=False):
        group = group.set_index(TARGET_DATETIME_COL)
        full_index = pd.date_range(group.index.min(), group.index.max(), freq="h")
        group = group.reindex(full_index)
        group[TARGET_STATION_COL] = station
        group[[TARGET_INFLOW_COL, TARGET_OUTFLOW_COL]] = group[[TARGET_INFLOW_COL, TARGET_OUTFLOW_COL]].fillna(0)
        reindexed_parts.append(group)

    full = pd.concat(reindexed_parts)
    full.index.name = TARGET_DATETIME_COL

    for lag in LAG_HOURS:
        full[f"inflow_lag_{lag}h"] = full.groupby(TARGET_STATION_COL)[TARGET_INFLOW_COL].shift(lag)

    for window in ROLLING_WINDOWS:
        full[f"inflow_rolling_mean_{window}h"] = (
            full.groupby(TARGET_STATION_COL)[TARGET_INFLOW_COL]
            .transform(lambda s: s.shift(1).rolling(window, min_periods=max(1, window // 4)).mean())
        )

    full[TARGET_COLUMN] = full.groupby(TARGET_STATION_COL)[TARGET_INFLOW_COL].shift(-PREDICTION_HORIZON_HOURS)

    full = full.reset_index()
    return add_calendar_features(full)


def build_feature_table(aggregated: pd.DataFrame, drop_incomplete_rows: bool = True) -> pd.DataFrame:
    """Full Step 2 feature pipeline: lag/rolling/calendar features + target column.

    Rows without enough history for the longest lag (168h) or without a valid
    next-hour target are dropped by default, since they can't be used for
    supervised training.
    """
    features = add_lag_and_rolling_features(aggregated)
    features = features.drop(columns=[c for c in ["日期", "時段"] if c in features.columns])
    if drop_incomplete_rows:
        lag_cols = [f"inflow_lag_{lag}h" for lag in LAG_HOURS]
        required_cols = lag_cols + [TARGET_COLUMN]
        features = features.dropna(subset=required_cols).reset_index(drop=True)
    return features
