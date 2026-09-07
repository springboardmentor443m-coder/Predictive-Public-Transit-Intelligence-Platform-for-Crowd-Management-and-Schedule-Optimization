"""Step 2 entry point: Feature Engineering for station-hourly demand forecasting.

Usage
-----
    python -m metroflow.features.run_feature_engineering [--file-limit N]

Pipeline:
  1. Stream over raw monthly OD files -> station-hourly inflow/outflow aggregate.
  2. Build lag, rolling-mean, and calendar features + the next-hour target column.
  3. Write the aggregated table and the final feature table to data/processed/.
  4. Write a feature engineering report to reports/feature_engineering_report.md.
"""
from __future__ import annotations

import argparse
import logging
import sys
from pathlib import Path

sys.path.append(str(Path(__file__).resolve().parents[3]))

from config.settings import (
    FEATURE_ENGINEERING_REPORT_MD_PATH,
    PROCESSED_DATA_DIR,
    STATION_HOURLY_AGG_PATH,
    STATION_HOURLY_FEATURES_PATH,
    TARGET_STATION_COL,
)
from metroflow.features.aggregator import build_station_hourly_aggregate
from metroflow.features.feature_builder import LAG_HOURS, ROLLING_WINDOWS, TARGET_COLUMN, build_feature_table

logging.basicConfig(level=logging.INFO, format="%(asctime)s [%(levelname)s] %(message)s")
logger = logging.getLogger("metroflow.feature_engineering")


def write_report(aggregated_shape: tuple[int, int], feature_shape: tuple[int, int], n_stations: int) -> None:
    lines = [
        "# MetroFlow — Step 2 Feature Engineering Report",
        "",
        "## ML Problem",
        "- Target: `target_inflow_next_hour` — station-level passenger inflow (people "
        "tapping out at that station) one hour ahead.",
        "- Unit of prediction: total passenger trip count for one station, for one future hour.",
        "- Prediction horizon: t+1 hour.",
        "",
        "## Aggregation",
        f"- Raw OD-pair rows collapsed to station-hourly rows: {aggregated_shape[0]:,} rows, "
        f"{aggregated_shape[1]} columns, across {n_stations} stations.",
        "- inflow = sum(人次) grouped by (出站, date, hour); outflow = sum(人次) grouped by (進站, date, hour).",
        "",
        "## Features engineered",
        f"- Lag features on inflow: {LAG_HOURS} hours back.",
        f"- Rolling mean features on inflow: {ROLLING_WINDOWS}-hour windows (computed on lagged values only, "
        "no leakage from the current/future hour).",
        "- Calendar features: hour_of_day, day_of_week, is_weekend, month, is_morning_peak, is_evening_peak.",
        "- outflow (same-hour) is included as a contextual feature, not as a lag, since it is observed "
        "at the same hour as the input row (not the future target hour).",
        "",
        "## Final feature table",
        f"- Shape after dropping rows without full lag history or a valid target: "
        f"{feature_shape[0]:,} rows, {feature_shape[1]} columns.",
        "",
        "## Files written",
        f"- `{STATION_HOURLY_AGG_PATH.relative_to(STATION_HOURLY_AGG_PATH.parents[2])}` — station-hourly aggregate.",
        f"- `{STATION_HOURLY_FEATURES_PATH.relative_to(STATION_HOURLY_FEATURES_PATH.parents[2])}` — final feature table.",
        "",
        "## Assumptions / limitations",
        "- Per-station hourly time index is reindexed to a complete hourly range between that "
        "station's first and last observed timestamp, filling missing hours with 0 trips, so lag "
        "features are computed against true elapsed time rather than against sparse observed rows.",
        "- No model has been trained yet — this step only prepares the supervised learning table.",
    ]
    FEATURE_ENGINEERING_REPORT_MD_PATH.write_text("\n".join(lines), encoding="utf-8")


def main(file_limit: int | None) -> None:
    PROCESSED_DATA_DIR.mkdir(parents=True, exist_ok=True)

    logger.info("Building station-hourly aggregate (file_limit=%s)...", file_limit)
    aggregated = build_station_hourly_aggregate(file_limit=file_limit)
    logger.info("Aggregated shape: %s", aggregated.shape)
    aggregated.to_parquet(STATION_HOURLY_AGG_PATH, index=False)
    logger.info("Wrote aggregate to %s", STATION_HOURLY_AGG_PATH)

    logger.info("Building feature table...")
    features = build_feature_table(aggregated)
    logger.info("Feature table shape: %s", features.shape)
    features.to_parquet(STATION_HOURLY_FEATURES_PATH, index=False)
    logger.info("Wrote feature table to %s", STATION_HOURLY_FEATURES_PATH)

    n_stations = aggregated[TARGET_STATION_COL].nunique()
    write_report(aggregated.shape, features.shape, n_stations)
    logger.info("Wrote feature engineering report to %s", FEATURE_ENGINEERING_REPORT_MD_PATH)


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="MetroFlow Step 2: Feature Engineering")
    parser.add_argument(
        "--file-limit",
        type=int,
        default=None,
        help="Optional cap on number of monthly raw files to process (for quick iteration).",
    )
    args = parser.parse_args()
    main(args.file_limit)
