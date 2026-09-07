"""Aggregate the raw OD-level dataset into station-hourly inflow/outflow.

The raw dataset is 705M+ OD-pair rows (entry station x exit station x date x
hour). For the chosen ML problem — station-level hourly passenger demand
forecasting — we don't need OD-pair granularity, only, per station and hour:

    inflow  = sum of trips where this station is the EXIT (出站) station
    outflow = sum of trips where this station is the ENTRY (進站) station

Aggregating collapses ~705M rows down to ~ (n_stations * n_days * 24 hours),
which fits comfortably in memory, so this is done once per raw file
(streaming) and the partial sums are combined.
"""
from __future__ import annotations

import logging
import sys
from pathlib import Path

import pandas as pd

sys.path.append(str(Path(__file__).resolve().parents[3]))
from config.settings import (
    COL_DATE,
    COL_ENTRY_STATION,
    COL_EXIT_STATION,
    COL_HOUR,
    COL_TRIP_COUNT,
    TARGET_DATETIME_COL,
    TARGET_INFLOW_COL,
    TARGET_OUTFLOW_COL,
    TARGET_STATION_COL,
)
from metroflow.data.loader import discover_raw_files, load_single_file

logger = logging.getLogger("metroflow.features.aggregator")


def _aggregate_one_file(df: pd.DataFrame) -> pd.DataFrame:
    """Return station-hourly inflow/outflow sums for a single monthly file."""
    inflow = (
        df.groupby([COL_EXIT_STATION, COL_DATE, COL_HOUR], observed=True)[COL_TRIP_COUNT]
        .sum()
        .rename(TARGET_INFLOW_COL)
        .reset_index()
        .rename(columns={COL_EXIT_STATION: TARGET_STATION_COL})
    )
    outflow = (
        df.groupby([COL_ENTRY_STATION, COL_DATE, COL_HOUR], observed=True)[COL_TRIP_COUNT]
        .sum()
        .rename(TARGET_OUTFLOW_COL)
        .reset_index()
        .rename(columns={COL_ENTRY_STATION: TARGET_STATION_COL})
    )
    merged = pd.merge(
        inflow,
        outflow,
        on=[TARGET_STATION_COL, COL_DATE, COL_HOUR],
        how="outer",
    )
    merged[[TARGET_INFLOW_COL, TARGET_OUTFLOW_COL]] = merged[[TARGET_INFLOW_COL, TARGET_OUTFLOW_COL]].fillna(0)
    return merged


def build_station_hourly_aggregate(file_limit: int | None = None) -> pd.DataFrame:
    """Stream over raw monthly files and build the station-hourly inflow/outflow table.

    Returns a DataFrame with columns: station, 日期, 時段, inflow, outflow.
    """
    files = discover_raw_files()
    if file_limit is not None:
        files = files[:file_limit]

    partials: list[pd.DataFrame] = []
    for i, file_path in enumerate(files, start=1):
        df = load_single_file(file_path)
        logger.info("[%d/%d] aggregating %s (%d rows)", i, len(files), file_path.name, len(df))
        partials.append(_aggregate_one_file(df))
        del df

    combined = pd.concat(partials, ignore_index=True)
    # A station can appear in multiple monthly files' outer-merge with duplicate
    # (station, date, hour) rows only if the same month's file produced both an
    # inflow-only and outflow-only row for it; re-aggregate defensively.
    combined = (
        combined.groupby([TARGET_STATION_COL, COL_DATE, COL_HOUR], as_index=False)[
            [TARGET_INFLOW_COL, TARGET_OUTFLOW_COL]
        ].sum()
    )
    combined[TARGET_DATETIME_COL] = pd.to_datetime(combined[COL_DATE]) + pd.to_timedelta(
        combined[COL_HOUR], unit="h"
    )
    combined = combined.sort_values([TARGET_STATION_COL, TARGET_DATETIME_COL]).reset_index(drop=True)
    return combined
