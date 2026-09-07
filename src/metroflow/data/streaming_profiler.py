"""Memory-safe, file-by-file profiling for the full Taipei MRT dataset.

The full raw dataset spans 85 monthly files (~640M OD records). Concatenating
every file into a single in-memory DataFrame is not practical on a typical
workstation, so this module computes the same profiling statistics as
``profiler.py`` incrementally, processing one monthly file at a time and
accumulating running totals.

Duplicate detection is performed within each monthly file (not across the
full 640M-row dataset), since each file already corresponds to one distinct
month and cross-file exact-duplicate checking would require hashing every
row into memory. This is documented as a known limitation of the streaming
report.
"""
from __future__ import annotations

import sys
from pathlib import Path
from typing import Any

import logging

import numpy as np
import pandas as pd

sys.path.append(str(Path(__file__).resolve().parents[3]))

logger = logging.getLogger("metroflow.profiling.streaming")
from config.settings import (
    COL_DATE,
    COL_ENTRY_STATION,
    COL_EXIT_STATION,
    COL_HOUR,
    COL_TRIP_COUNT,
)
from metroflow.data.loader import discover_raw_files, load_single_file


class _RunningStats:
    """Accumulates count/sum/sumsq/min/max for a numeric series across chunks."""

    def __init__(self) -> None:
        self.n = 0
        self.total = 0.0
        self.total_sq = 0.0
        self.min = np.inf
        self.max = -np.inf
        self.n_zero = 0
        self.n_negative = 0
        self.value_counts: dict[int, int] = {}

    def update(self, series: pd.Series) -> None:
        self.n += len(series)
        self.total += float(series.sum())
        self.total_sq += float((series.astype("float64") ** 2).sum())
        self.min = min(self.min, float(series.min()))
        self.max = max(self.max, float(series.max()))
        self.n_zero += int((series == 0).sum())
        self.n_negative += int((series < 0).sum())

    def summary(self) -> dict[str, Any]:
        mean = self.total / self.n if self.n else float("nan")
        variance = (self.total_sq / self.n - mean**2) if self.n else float("nan")
        std = float(np.sqrt(max(variance, 0.0)))
        return {
            "min": self.min,
            "max": self.max,
            "mean": mean,
            "std": std,
            "n_zero": self.n_zero,
            "n_negative": self.n_negative,
            "note": "median/percentiles omitted in streaming mode (would require full sort of 640M+ values)",
        }


def run_streaming_profile(file_limit: int | None = None) -> dict[str, Any]:
    files = discover_raw_files()
    if file_limit is not None:
        files = files[:file_limit]

    n_rows_total = 0
    n_missing = {COL_DATE: 0, COL_HOUR: 0, COL_ENTRY_STATION: 0, COL_EXIT_STATION: 0, COL_TRIP_COUNT: 0}
    n_duplicate_rows_total = 0
    trip_stats = _RunningStats()
    entry_stations: set[str] = set()
    exit_stations: set[str] = set()
    hour_values: set[int] = set()
    min_date: str | None = None
    max_date: str | None = None
    n_same_station_od = 0
    per_file_row_counts: dict[str, int] = {}

    for i, file_path in enumerate(files, start=1):
        df = load_single_file(file_path)
        logger.info("[%d/%d] processing %s (%d rows)", i, len(files), file_path.name, len(df))
        per_file_row_counts[file_path.name] = len(df)
        n_rows_total += len(df)

        for col in n_missing:
            n_missing[col] += int(df[col].isna().sum())

        dup_mask = df.duplicated(subset=[COL_DATE, COL_HOUR, COL_ENTRY_STATION, COL_EXIT_STATION])
        n_duplicate_rows_total += int(dup_mask.sum())

        trip_stats.update(df[COL_TRIP_COUNT])
        entry_stations.update(df[COL_ENTRY_STATION].unique())
        exit_stations.update(df[COL_EXIT_STATION].unique())
        hour_values.update(df[COL_HOUR].unique().tolist())
        n_same_station_od += int((df[COL_ENTRY_STATION] == df[COL_EXIT_STATION]).sum())

        file_dates = pd.to_datetime(df[COL_DATE], errors="coerce").dropna()
        if not file_dates.empty:
            file_min, file_max = str(file_dates.min().date()), str(file_dates.max().date())
            min_date = file_min if min_date is None else min(min_date, file_min)
            max_date = file_max if max_date is None else max(max_date, file_max)

        del df

    all_stations = entry_stations | exit_stations
    zero_pct = trip_stats.n_zero / n_rows_total * 100 if n_rows_total else 0.0

    issues: list[str] = []
    if trip_stats.n_negative:
        issues.append(f"{trip_stats.n_negative} rows have negative passenger counts.")
    if n_same_station_od:
        issues.append(
            f"{n_same_station_od} rows have identical entry and exit station "
            "(same-station OD pairs; may represent self-loops/placeholder rows, not errors)."
        )
    if zero_pct > 20:
        issues.append(
            f"{zero_pct:.1f}% of rows have zero passenger count — expected given the dense "
            "station OD matrix per hour, but relevant for modeling (heavy zero-inflation)."
        )
    if len(hour_values) < 24:
        issues.append(f"Only {len(hour_values)}/24 distinct hour values observed across the dataset.")
    if n_duplicate_rows_total:
        issues.append(
            f"{n_duplicate_rows_total} within-file duplicate (date, hour, entry, exit) rows detected."
        )

    return {
        "dimensions": {"n_rows": n_rows_total, "n_columns": 5},
        "missing_values": n_missing,
        "duplicates": {"n_duplicate_rows_within_file": n_duplicate_rows_total},
        "numerical_statistics": {COL_TRIP_COUNT: trip_stats.summary()},
        "categorical_cardinality": {
            "n_unique_entry_stations": len(entry_stations),
            "n_unique_exit_stations": len(exit_stations),
            "n_unique_hour_values": len(hour_values),
            "hour_value_range": [min(hour_values), max(hour_values)] if hour_values else None,
        },
        "datetime_coverage": {"min_date": min_date, "max_date": max_date},
        "station_coverage": {
            "n_total_unique_stations": len(all_stations),
            "n_entry_only_stations": len(entry_stations - exit_stations),
            "n_exit_only_stations": len(exit_stations - entry_stations),
        },
        "data_quality_issues": issues,
        "per_file_row_counts": per_file_row_counts,
        "n_files_processed": len(files),
    }
