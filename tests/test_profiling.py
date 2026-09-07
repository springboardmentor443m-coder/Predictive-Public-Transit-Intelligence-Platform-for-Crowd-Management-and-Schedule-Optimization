"""Tests for the Step 1 data ingestion & profiling workflow.

Run with: python -m pytest tests/test_profiling.py -v
"""
import sys
from pathlib import Path

import pandas as pd
import pytest

sys.path.append(str(Path(__file__).resolve().parent.parent / "src"))

from config.settings import COL_DATE, COL_ENTRY_STATION, COL_EXIT_STATION, COL_HOUR, COL_TRIP_COUNT
from metroflow.data.loader import discover_raw_files, load_raw_dataset, load_single_file
from metroflow.data.profiler import build_profile_report
from metroflow.data.streaming_profiler import run_streaming_profile


def test_discover_raw_files_finds_parquet_files():
    files = discover_raw_files()
    assert len(files) > 0
    assert all(f.name.endswith(".parquet.gzip") for f in files)


def test_load_single_file_has_expected_columns():
    files = discover_raw_files()
    df = load_single_file(files[0])
    for col in (COL_DATE, COL_HOUR, COL_ENTRY_STATION, COL_EXIT_STATION, COL_TRIP_COUNT):
        assert col in df.columns


def test_load_raw_dataset_respects_file_limit():
    df = load_raw_dataset(file_limit=1)
    single_file_rows = len(load_single_file(discover_raw_files()[0]))
    assert len(df) == single_file_rows


def test_build_profile_report_structure():
    df = load_raw_dataset(file_limit=1)
    report = build_profile_report(df)
    for key in (
        "dimensions",
        "columns",
        "missing_values",
        "duplicates",
        "numerical_statistics",
        "categorical_cardinality",
        "datetime_coverage",
        "station_coverage",
        "data_quality_issues",
    ):
        assert key in report
    assert report["dimensions"]["n_rows"] == len(df)


def test_trip_count_is_non_negative_in_sample():
    df = load_raw_dataset(file_limit=1)
    assert (df[COL_TRIP_COUNT] >= 0).all()


def test_hour_values_within_expected_range():
    df = load_raw_dataset(file_limit=1)
    assert df[COL_HOUR].min() >= 0
    assert df[COL_HOUR].max() <= 23


def test_streaming_profile_matches_in_memory_on_small_sample():
    n_files = 2
    streaming_report = run_streaming_profile(file_limit=n_files)
    df = load_raw_dataset(file_limit=n_files)
    in_memory_report = build_profile_report(df)

    assert streaming_report["dimensions"]["n_rows"] == in_memory_report["dimensions"]["n_rows"]
    assert (
        streaming_report["categorical_cardinality"]["n_unique_entry_stations"]
        == in_memory_report["categorical_cardinality"]["n_unique_entry_stations"]
    )


def test_raw_files_are_not_modified_by_profiling():
    files = discover_raw_files()
    sample = files[0]
    size_before = sample.stat().st_size
    mtime_before = sample.stat().st_mtime
    load_single_file(sample)
    assert sample.stat().st_size == size_before
    assert sample.stat().st_mtime == mtime_before
