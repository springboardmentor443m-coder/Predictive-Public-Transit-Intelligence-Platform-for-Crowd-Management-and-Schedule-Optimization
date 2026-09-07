# MetroFlow — Dataset Capability Analysis & ML Problem Definition

This document covers instructions.txt sections 4 ("Determine the actual data structure
before designing the ML pipeline") and 6 ("Decide the initial ML problem"), based on the
full-dataset profiling (`reports/profiling_report.md`) and feature engineering
(`reports/feature_engineering_report.md`) already completed.

## 1. What the dataset directly supports

The raw dataset is a dense hourly origin-destination (OD) passenger-count matrix:
`(日期 date, 時段 hour, 進站 entry station, 出站 exit station, 人次 trip count)`,
705,206,450 rows, 122 stations, hourly granularity, 2017-01-01 to 2024-01-31.

Directly supported, with no assumptions beyond what's in the columns:
- **Historical passenger volume analysis** per station, per hour, per day.
- **Passenger inflow/outflow analysis** — inflow (people exiting at a station) and
  outflow (people entering at a station) are directly computable via groupby/sum.
- **Peak-hour analysis** — hour-of-day is a native column; peak periods are directly
  observable from aggregated volumes.
- **Station-level historical demand forecasting** — station + hourly timestamp +
  trip count is exactly the shape needed for a time-series supervised learning table.
- **OD-pair-level trip counts** (e.g. "how many people went from Station A to Station B
  at 8am on Mondays") — supported but very sparse (108x108 pairs per hour, ~40% zero).

## 2. What can reasonably be derived through feature engineering

Implemented in Step 2 (`src/metroflow/features/`):
- Station-level hourly **inflow/outflow aggregates** (collapsing the sparse OD matrix).
- **Lag features** (t-1h, t-2h, t-3h, t-24h, t-168h) and **rolling means** (24h, 168h)
  per station, computed on a gap-filled complete hourly time index.
- **Calendar features**: hour-of-day, day-of-week, weekend flag, month, morning/evening
  peak flags — all derivable from the `日期`/`時段` columns alone.
- **Congestion proxies**: relative volume vs. a station's own rolling average can be
  derived (e.g. inflow / rolling_mean_168h) as an approximate congestion indicator,
  since no direct capacity or occupancy figure exists in the data.

## 3. What cannot be reliably implemented from this dataset alone

Per the PDF's own note ("The platform does not use computer vision or CCTV image
processing") and the actual dataset contents, the following PDF-described capabilities
require data sources that are **not present** in this dataset and must not be fabricated:

- **Real train occupancy / capacity-based congestion** — no train occupancy records,
  no seat/carriage capacity figures exist. Any "% full" or true congestion-severity
  metric would be fabricated without an external capacity dataset.
- **Train GPS / real-time position, schedule, or delay data** — no GPS, schedule, or
  delay logs exist in this dataset. Delay-handling, real-time train status, and
  frequency-adjustment features described in the PDF's Scheduling Module cannot be
  built from this dataset alone.
- **Ticketing-system-level individual passenger records** — the dataset is already
  pre-aggregated to hourly OD counts; no smart-card/individual-trip-level data exists,
  so anything requiring individual passenger trajectories is out of scope.
- **Live/real-time sensor feeds** — the dataset is historical batch data (monthly
  files through 2024-01), not a live stream; a real-time monitoring module would need
  a separate live data source, with this dataset only useful for historical model
  training.

These gaps do not block Step 1/2 (data profiling and demand-forecasting feature
engineering) but do bound what the later AI Prediction and Scheduling modules can
honestly claim to do with this data source alone.

## 4. Recommended ML problem (decision)

- **Target variable:** `target_inflow_next_hour` — a station's total passenger inflow
  (people tapping out / exiting at that station) for the next hour.
- **Prediction horizon:** t+1 hour (one hour ahead), the finest horizon the data's
  hourly granularity supports without extrapolation.
- **Unit of prediction:** total passenger trip count (integer/count, currently summed
  from `人次`) for one station, for one future hour.
- **Important input features:** `inflow_lag_1h/2h/3h/24h/168h`, `inflow_rolling_mean_24h/168h`,
  same-hour `outflow`, `hour_of_day`, `day_of_week`, `is_weekend`, `month`,
  `is_morning_peak`, `is_evening_peak` (see `reports/feature_engineering_report.md`).
- **Why this target is appropriate for MetroFlow:**
  - It is directly supported by the dataset (no fabricated inputs).
  - It matches the PDF's "Demand Forecasting" and "Peak-hour forecasting" outcomes
    (AI Prediction Module) using only ridership data, consistent with the PDF's
    explicit note that ridership-data-based density estimation (not CCTV) is the
    intended approach.
  - Station-level (not OD-pair-level) granularity is chosen because OD-pair volumes
    are heavily zero-inflated (~40% zero) and noisy; station-level aggregates give a
    denser, more learnable signal while still supporting station-wise analytics,
    congestion monitoring, and per-station alerting envisioned by the PDF.
  - A 1-hour horizon is operationally useful for crowd/overcrowding alerts and
    schedule-frequency recommendations without requiring assumptions the data can't
    support (e.g. multi-day-ahead forecasts would need external calendar/event data
    not present here).
