# MetroFlow — Step 2 Feature Engineering Report

## ML Problem
- Target: `target_inflow_next_hour` — station-level passenger inflow (people tapping out at that station) one hour ahead.
- Unit of prediction: total passenger trip count for one station, for one future hour.
- Prediction horizon: t+1 hour.

## Aggregation
- Raw OD-pair rows collapsed to station-hourly rows: 6,230,504 rows, 6 columns, across 122 stations.
- inflow = sum(人次) grouped by (出站, date, hour); outflow = sum(人次) grouped by (進站, date, hour).

## Features engineered
- Lag features on inflow: [1, 2, 3, 24, 168] hours back.
- Rolling mean features on inflow: [24, 168]-hour windows (computed on lagged values only, no leakage from the current/future hour).
- Calendar features: hour_of_day, day_of_week, is_weekend, month, is_morning_peak, is_evening_peak.
- outflow (same-hour) is included as a contextual feature, not as a lag, since it is observed at the same hour as the input row (not the future target hour).

## Final feature table
- Shape after dropping rows without full lag history or a valid target: 7,097,062 rows, 18 columns.

## Files written
- `data\processed\station_hourly_aggregated.parquet` — station-hourly aggregate.
- `data\processed\station_hourly_features.parquet` — final feature table.

## Assumptions / limitations
- Per-station hourly time index is reindexed to a complete hourly range between that station's first and last observed timestamp, filling missing hours with 0 trips, so lag features are computed against true elapsed time rather than against sparse observed rows.
- No model has been trained yet — this step only prepares the supervised learning table.