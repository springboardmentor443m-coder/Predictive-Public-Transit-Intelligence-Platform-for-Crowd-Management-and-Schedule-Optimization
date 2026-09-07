"""Data profiling logic for the raw Taipei MRT hourly OD dataset.

Each ``analyze_*`` function inspects a DataFrame (already loaded, never
mutated) and returns a plain-dict summary. ``build_profile_report``
assembles all of them into one structured report.
"""
from __future__ import annotations

import sys
from pathlib import Path
from typing import Any

import numpy as np
import pandas as pd

sys.path.append(str(Path(__file__).resolve().parents[3]))
from config.settings import (
    COL_DATE,
    COL_ENTRY_STATION,
    COL_EXIT_STATION,
    COL_HOUR,
    COL_TRIP_COUNT,
)


def analyze_dimensions(df: pd.DataFrame) -> dict[str, Any]:
    return {"n_rows": int(df.shape[0]), "n_columns": int(df.shape[1])}


def analyze_columns(df: pd.DataFrame) -> dict[str, Any]:
    return {
        col: {
            "dtype": str(df[col].dtype),
            "n_unique": int(df[col].nunique(dropna=True)),
        }
        for col in df.columns
    }


def analyze_missing_values(df: pd.DataFrame) -> dict[str, Any]:
    missing_counts = df.isna().sum()
    missing_pct = (missing_counts / len(df) * 100).round(4)
    return {
        col: {"missing_count": int(missing_counts[col]), "missing_pct": float(missing_pct[col])}
        for col in df.columns
    }


def analyze_duplicates(df: pd.DataFrame) -> dict[str, Any]:
    dup_mask = df.duplicated(subset=[COL_DATE, COL_HOUR, COL_ENTRY_STATION, COL_EXIT_STATION])
    return {
        "n_duplicate_rows": int(dup_mask.sum()),
        "duplicate_pct": float(round(dup_mask.sum() / len(df) * 100, 4)),
    }


def analyze_numerical_statistics(df: pd.DataFrame) -> dict[str, Any]:
    trips = df[COL_TRIP_COUNT]
    return {
        "min": float(trips.min()),
        "max": float(trips.max()),
        "mean": float(trips.mean()),
        "std": float(trips.std()),
        "median": float(trips.median()),
        "p95": float(trips.quantile(0.95)),
        "p99": float(trips.quantile(0.99)),
        "n_zero": int((trips == 0).sum()),
        "n_negative": int((trips < 0).sum()),
    }


def analyze_categorical_cardinality(df: pd.DataFrame) -> dict[str, Any]:
    return {
        "n_unique_entry_stations": int(df[COL_ENTRY_STATION].nunique()),
        "n_unique_exit_stations": int(df[COL_EXIT_STATION].nunique()),
        "n_unique_hour_values": int(df[COL_HOUR].nunique()),
        "hour_value_range": [int(df[COL_HOUR].min()), int(df[COL_HOUR].max())],
    }


def analyze_datetime_coverage(df: pd.DataFrame) -> dict[str, Any]:
    dates = pd.to_datetime(df[COL_DATE], errors="coerce")
    n_unparseable = int(dates.isna().sum())
    valid_dates = dates.dropna()
    all_days = pd.date_range(valid_dates.min(), valid_dates.max(), freq="D")
    observed_days = set(valid_dates.dt.normalize().unique())
    missing_days = sorted(d.strftime("%Y-%m-%d") for d in all_days if d not in observed_days)
    return {
        "min_date": str(valid_dates.min().date()) if not valid_dates.empty else None,
        "max_date": str(valid_dates.max().date()) if not valid_dates.empty else None,
        "n_unparseable_dates": n_unparseable,
        "n_calendar_days_in_range": int(len(all_days)),
        "n_days_observed": int(len(observed_days)),
        "n_days_missing": len(missing_days),
        "sample_missing_days": missing_days[:20],
        "hour_granularity": "hourly (0-23, with irregular gaps observed per station-day)",
    }


def analyze_station_coverage(df: pd.DataFrame) -> dict[str, Any]:
    entry_stations = set(df[COL_ENTRY_STATION].unique())
    exit_stations = set(df[COL_EXIT_STATION].unique())
    all_stations = entry_stations | exit_stations
    return {
        "n_total_unique_stations": len(all_stations),
        "n_entry_only_stations": len(entry_stations - exit_stations),
        "n_exit_only_stations": len(exit_stations - entry_stations),
        "stations_sample": sorted(list(all_stations))[:15],
    }


def identify_data_quality_issues(df: pd.DataFrame) -> list[str]:
    issues: list[str] = []
    trips = df[COL_TRIP_COUNT]

    if (trips < 0).any():
        issues.append(f"{int((trips < 0).sum())} rows have negative passenger counts.")

    same_station_od = df[df[COL_ENTRY_STATION] == df[COL_EXIT_STATION]]
    if not same_station_od.empty:
        issues.append(
            f"{len(same_station_od)} rows have identical entry and exit station "
            "(same-station OD pairs; may represent self-loops/placeholder rows, not errors)."
        )

    zero_pct = (trips == 0).sum() / len(df) * 100
    if zero_pct > 20:
        issues.append(
            f"{zero_pct:.1f}% of rows have zero passenger count — expected given the dense "
            "108x108 station OD matrix per hour (most OD pairs are rarely used), but worth "
            "noting for downstream modeling (heavy zero-inflation)."
        )

    n_hours = df[COL_HOUR].nunique()
    if n_hours < 24:
        issues.append(
            f"Only {n_hours}/24 distinct hour values observed in this slice — some hours "
            "(e.g. late-night maintenance hours) may be structurally absent from the source data."
        )

    if df[COL_ENTRY_STATION].isna().any() or df[COL_EXIT_STATION].isna().any():
        issues.append("Missing station names found in entry/exit columns.")

    return issues


def build_profile_report(df: pd.DataFrame) -> dict[str, Any]:
    """Assemble the full structured profiling report for the given DataFrame."""
    return {
        "dimensions": analyze_dimensions(df),
        "columns": analyze_columns(df),
        "missing_values": analyze_missing_values(df),
        "duplicates": analyze_duplicates(df),
        "numerical_statistics": {COL_TRIP_COUNT: analyze_numerical_statistics(df)},
        "categorical_cardinality": analyze_categorical_cardinality(df),
        "datetime_coverage": analyze_datetime_coverage(df),
        "station_coverage": analyze_station_coverage(df),
        "data_quality_issues": identify_data_quality_issues(df),
    }
