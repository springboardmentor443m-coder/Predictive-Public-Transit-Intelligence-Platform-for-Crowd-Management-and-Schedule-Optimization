"""Tests for the Step 2 feature engineering workflow.

Run with: python -m pytest tests/test_feature_engineering.py -v
"""
import sys
from pathlib import Path

import pandas as pd

sys.path.append(str(Path(__file__).resolve().parent.parent / "src"))

from config.settings import TARGET_INFLOW_COL, TARGET_OUTFLOW_COL, TARGET_STATION_COL
from metroflow.features.aggregator import build_station_hourly_aggregate
from metroflow.features.feature_builder import LAG_HOURS, TARGET_COLUMN, build_feature_table


def test_aggregate_has_expected_columns():
    agg = build_station_hourly_aggregate(file_limit=1)
    for col in (TARGET_STATION_COL, TARGET_INFLOW_COL, TARGET_OUTFLOW_COL, "datetime"):
        assert col in agg.columns


def test_aggregate_inflow_outflow_non_negative():
    agg = build_station_hourly_aggregate(file_limit=1)
    assert (agg[TARGET_INFLOW_COL] >= 0).all()
    assert (agg[TARGET_OUTFLOW_COL] >= 0).all()


def test_aggregate_matches_raw_totals():
    # Sum of station-hourly inflow must equal sum of raw trip counts (no rows lost).
    import metroflow.data.loader as loader_module

    files = loader_module.discover_raw_files()
    raw = loader_module.load_single_file(files[0])
    raw_total = raw["人次"].sum()

    agg = build_station_hourly_aggregate(file_limit=1)
    assert agg[TARGET_INFLOW_COL].sum() == raw_total
    assert agg[TARGET_OUTFLOW_COL].sum() == raw_total


def test_feature_table_has_no_nulls_in_required_columns():
    agg = build_station_hourly_aggregate(file_limit=2)
    features = build_feature_table(agg)
    required = [f"inflow_lag_{lag}h" for lag in LAG_HOURS] + [TARGET_COLUMN]
    assert not features[required].isna().any().any()


def test_target_is_shifted_inflow():
    agg = build_station_hourly_aggregate(file_limit=2)
    features = build_feature_table(agg, drop_incomplete_rows=False)
    one_station = features[features[TARGET_STATION_COL] == features[TARGET_STATION_COL].iloc[0]].sort_values(
        "datetime"
    )
    # target at row i should equal inflow at row i+1 (t+1 horizon)
    shifted_inflow = one_station[TARGET_INFLOW_COL].shift(-1)
    comparison = one_station[TARGET_COLUMN].iloc[:-1].reset_index(drop=True)
    expected = shifted_inflow.iloc[:-1].reset_index(drop=True)
    assert comparison.equals(expected)


def test_lag_features_use_only_past_values():
    agg = build_station_hourly_aggregate(file_limit=2)
    features = build_feature_table(agg, drop_incomplete_rows=False)
    one_station = features[features[TARGET_STATION_COL] == features[TARGET_STATION_COL].iloc[0]].sort_values(
        "datetime"
    )
    non_null = one_station.dropna(subset=["inflow_lag_1h"])
    shifted = one_station[TARGET_INFLOW_COL].shift(1)
    pd.testing.assert_series_equal(
        non_null["inflow_lag_1h"].reset_index(drop=True),
        shifted.loc[non_null.index].reset_index(drop=True),
        check_names=False,
    )
