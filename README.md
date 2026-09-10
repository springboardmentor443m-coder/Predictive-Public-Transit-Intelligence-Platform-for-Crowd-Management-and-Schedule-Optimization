# MetroFlow Seoul — AI Metro Crowd Management & Scheduling

MetroFlow is a working Milestone 1 & 2 prototype built around the **actual Seoul Metro 2015 passenger-flow log supplied for this project**.

## Dataset used
File: `data/seoul-metro-2015.logs.csv`

The supplied file contains:
- 2,007,500 records
- 275 station codes
- timestamps from 2015-01-01 05:00 KST through 2016-01-01 00:00 KST
- `timestamp`
- `station_code`
- `people_in`
- `people_out`

The dataset is a refined Seoul Metro usage dataset. Public documentation for this dataset states that its yearly log files use `station_code` to join station metadata and contain hourly station boarding/alighting records. It covers Seoul Metro Lines 1–8. See the project source reference in `docs/data_source.md`.

## Milestone 1 — Week 1 & 2
Aligned to the project brief:
- Project initialization and architecture
- Role-based authentication (Admin / Operator)
- Crowd monitoring dashboard
- Station-wise passenger flow
- Line-wise filtering
- Peak-hour analysis
- Database/schema planning
- UI/workflow documentation

## Milestone 2 — Week 3 & 4
- AI passenger-flow prediction
- Random Forest regression
- Model evaluation (MAE, RMSE, R²)
- Train-frequency recommendation
- Peak-demand analysis
- Traffic analysis report
- CSV report export
- Operational monitoring view

## Important timetable note
The supplied passenger-flow log does **not** contain actual train arrival/departure timetable fields. MetroFlow therefore does not invent real train timings. Instead, the Schedule Planner provides an **AI frequency/headway recommendation** from predicted passenger demand and shows the observed passenger-activity window.

## Run
```bash
python -m venv venv
venv\Scripts\activate
pip install -r requirements.txt
streamlit run app/streamlit_app.py
```

Demo login:
- Admin: `admin` / `admin123`
- Operator: `operator` / `operator123`

## Folder structure
```text
MetroFlow_Seoul_Project
│   └── streamlit_app.py
├── data/
│   ├── seoul-metro-2015.logs.csv
│   └── hourly_line_summary.csv
├── docs/
│   ├── architecture.md
│   ├── database_schema.md
│   ├── milestone_report.md
│   └── data_source.md
├── models/
│   ├── crowd_forecast_rf.joblib
│   └── metrics.json
├── requirements.txt
└── README.md
```
