# MetroFlow — Data Dictionary (Taipei MRT Hourly OD Dataset)

Source: Kaggle "Taipei MRT Hourly Traffic Data" (`archive/*.parquet.gzip`), 85 monthly
files covering 2017-01 through 2024-01. Each row is an hourly origin-destination (OD)
passenger count between a pair of MRT stations. Raw column names are in Traditional
Chinese, as provided by the source; they are not renamed on disk.

| Column | Data Type | Meaning | Missing Values | Role |
| --- | --- | --- | --- | --- |
| 日期 (date) | object (string, `YYYY-MM-DD`) | Calendar date of the trip record | None observed | Time feature |
| 時段 (hour) | int64 (0–23) | Hour-of-day bucket the trip was recorded in | None observed | Time feature |
| 進站 (entry_station) | object (string) | Station name where the passenger tapped in | None observed | Identifier / Categorical feature |
| 出站 (exit_station) | object (string) | Station name where the passenger tapped out | None observed | Identifier / Categorical feature |
| 人次 (trip_count) | int64 | Number of passengers for this (date, hour, entry, exit) combination | None observed | Potential target / Numerical feature |
| source_file | object (added by loader, not in raw file) | Name of the monthly parquet file the row came from | N/A | Not useful for modeling (provenance only) |

## Notes

- The dataset is a dense OD matrix: for every hour of every day, most of the 108×108
  station pairs are present with a `人次` value, including `0` when no passengers made
  that specific trip. This produces heavy zero-inflation (~35%+ of rows are 0).
- `進站 == 出站` (same-station OD) rows exist and are not treated as errors — they may
  represent tap-in/tap-out anomalies or short-loop trips recorded by the ticketing
  system; they are flagged in the profiling report for visibility, not removed.
- There is no train occupancy, GPS, sensor, delay, or CCTV data in this dataset. Any
  MetroFlow module described in the project documentation that depends on those data
  sources (train occupancy records, GPS/status data, delay logs) cannot be built from
  this dataset alone and would require additional data sources.
- `archive/tpe_mrt_lines.json` and `archive/newtpe_mrt_lines.json` provide station-to-line
  metadata (line code, sequence, English names) and can be joined on station name for
  richer station-level features (line, sequence) in later feature engineering steps.
