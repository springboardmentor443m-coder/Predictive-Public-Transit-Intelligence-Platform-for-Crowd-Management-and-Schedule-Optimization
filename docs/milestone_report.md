# Milestone 1 & 2 Report

## Milestone 1
### Objective
Build the foundation of an AI metro crowd-management platform.

### Completed
- Streamlit application initialized.
- Admin/operator authentication implemented.
- Seoul passenger-flow dataset loaded.
- Crowd monitoring dashboard implemented.
- Line and station filters implemented.
- Daily and hourly passenger-flow charts implemented.
- Peak-hour monitoring implemented.
- Top station-code ranking implemented.
- Architecture and logical database schema documented.

### Evidence
Dashboard metrics include entries, exits, peak hour and peak flow. The application provides daily and hourly trend charts and station-level comparisons.

## Milestone 2
### Objective
Add scheduling workflows and AI prediction.

### Completed
- Random Forest passenger-flow model.
- Time-aware train/test split.
- Model metrics stored in `models/metrics.json`.
- Demand prediction by station and hour.
- Crowd-risk classification.
- Frequency/headway recommendation.
- Traffic report generation and CSV download.
- Operational planning view.

### Model
Target:
`total_flow = people_in + people_out`

Features:
- station_code
- hour
- day_of_week
- month
- dayofyear
- weekofyear

The model was trained on the supplied real Seoul Metro records; no synthetic passenger records were generated.

### Current model metrics
See `models/metrics.json` for reproducible metrics from the packaged model.

## Limitation
The supplied dataset contains passenger-flow observations, not actual train arrival/departure schedule records. Therefore exact train times are not fabricated. The scheduling module is a demand-based frequency recommendation workflow. Exact timetable integration is a future data-source connection.
