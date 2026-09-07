# MetroFlow — Milestone 1: Project Setup, Data Ingestion & Profiling, Feature Engineering

MetroFlow is an AI platform for metro crowd management and scheduling. This
milestone covers the first three weeks of implementation: project
setup/architecture, data ingestion & profiling, and feature engineering.
Later milestones (model training, congestion/scheduling/alerts, analytics,
database, API, authentication, frontend) are tracked separately and are not
part of this commit.

## Dataset

Raw dataset: **Taipei MRT Hourly Traffic Data** (Kaggle), 85 monthly parquet
files covering 2017-01 through 2024-01, plus station/line metadata JSON
files. Expected local location: `archive/` at the project root (not
committed to this repository — see "Reproducing locally" below).

## Project structure

```
config/                  Path & column-name configuration (no hardcoded absolute paths)
archive/                 Raw Kaggle dataset (not committed; see below) — read-only
src/metroflow/data/
  loader.py              Read-only raw dataset loading
  profiler.py            In-memory profiling analyzers (small/sampled datasets)
  streaming_profiler.py  Memory-safe file-by-file profiling (full 85-file dataset)
  report_writer.py       Renders profiling report to JSON + Markdown
  run_profiling.py       CLI entry point for data ingestion & profiling
src/metroflow/features/
  aggregator.py          Streams raw OD data -> station-hourly inflow/outflow
  feature_builder.py     Lag, rolling-mean, calendar features + next-hour target
  run_feature_engineering.py  CLI entry point for feature engineering
notebooks/               Exploratory data analysis
reports/                 Generated data dictionary + profiling/feature-engineering reports
tests/                   Automated tests for the ingestion and feature-engineering workflows
```

## Running data ingestion & profiling

```bash
pip install -r requirements.txt
cd src
python -m metroflow.data.run_profiling            # full dataset, streaming mode (default)
python -m metroflow.data.run_profiling --file-limit 3 --mode in_memory   # quick local check
python -m pytest ../tests/test_profiling.py -v
```

Reports: `reports/profiling_report.json`, `reports/profiling_report.md`,
`reports/data_dictionary.md`.

## Running feature engineering

```bash
cd src
python -m metroflow.features.run_feature_engineering                # full dataset
python -m metroflow.features.run_feature_engineering --file-limit 3  # quick local check
python -m pytest ../tests/test_feature_engineering.py -v
```

Outputs:
- `data/processed/station_hourly_aggregated.parquet` — station x date x hour inflow/outflow.
- `data/processed/station_hourly_features.parquet` — lag/rolling/calendar features + target.
- `reports/feature_engineering_report.md` — summary of the feature pipeline.

**ML problem (recommended target):** predict `target_inflow_next_hour` — a
station's total passenger inflow one hour ahead — using lagged inflow
(1h/2h/3h/24h/168h), rolling means, same-hour outflow, and calendar features
(hour, day-of-week, weekend, peak-hour flags). See
`reports/ml_problem_definition.md` for the full dataset-capability analysis
and target/horizon justification.

## Reproducing locally

The raw dataset is not committed to this repository (large binary files).
To reproduce:
1. Download the Taipei MRT Hourly Traffic Data from Kaggle.
2. Place the monthly `.parquet.gzip` files and the station/line metadata
   JSON files under `archive/` at the project root.
3. Run the ingestion/profiling and feature-engineering commands above.

The raw dataset under `archive/` is never modified by any step.
