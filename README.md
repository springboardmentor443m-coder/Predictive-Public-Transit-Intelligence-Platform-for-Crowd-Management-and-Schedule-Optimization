# MetroFlow Seoul
**Predictive Public Transit Intelligence Platform for Crowd Management and Schedule Optimization**

A student-friendly full-stack project using **FastAPI + HTML/CSS/JavaScript**. It does not use Streamlit. The supplied compressed source dataset is included at `data/seoul-metro-2015.logs.csv.gz`.

## Dataset checked
- 2,007,500 rows and 4 required columns: `timestamp`, `station_code`, `people_in`, `people_out`
- 275 distinct station codes in the original source dataset; the dashboard deliberately analyses a deterministic subset of the first 20 sorted station codes to reduce processing time.
- Source time range: 2015-01-01 through 2016-01-01 (Asia/Seoul)
- Initial validation found no missing values in these columns
- Station codes are kept as codes; no unverified station-name mapping is assumed.

## Run on Windows
1. Extract the ZIP to a normal folder.
2. Install Python 3.10 or newer if it is not already installed.
3. Open Command Prompt in the extracted `MetroFlow_Seoul` folder.
4. Run:
   ```bat
   python -m venv .venv
   .venv\Scripts\activate
   pip install -r requirements.txt
   uvicorn backend.main:app --reload
   ```
5. Open **http://127.0.0.1:8000**. API documentation: **http://127.0.0.1:8000/docs**.

If you prefer not to create a virtual environment, run `pip install -r requirements.txt` and then `uvicorn backend.main:app --reload` from the project folder.

## Performance setting: 20 stations
The dashboard uses only the first 20 station codes in sorted order across **all** sections and APIs (overview, simulator, forecast, heatmap, alerts, analytics, and CSV export). The original compressed dataset is kept intact in the `data` folder. The subset is selected by station code, not by an assumed station-name mapping.

## Dashboard sections
- **Overview:** total entries/exits, station count, average flow, daily movement and high-flow observations.
- **Live simulator:** cycles through actual historical records at a short interval to demonstrate a changing operations feed.
- **Forecast & schedules:** transparent hour-of-day average baseline for the next 12 hours.
- **Crowd heatmap:** observed mean flow by station code and hour.
- **Alerts center:** high-flow observations, data-derived severity, and a demo announcement composer.
- **Analytics:** station rankings, hourly averages, and CSV export.

## Important limitation: historical vs live
The included source data is historical (2015), not a live 2026 Seoul Metro feed. The simulator continuously replays real rows from the supplied dataset; it does **not** fabricate new passenger counts or connect to live Seoul Metro operations. A real live feed would require an authorized, current data API. Forecasts are a baseline, not a validated production model. Alerts are illustrative and do not represent official capacity thresholds. Announcements are stored in memory for the running app only and are not broadcast to passengers.

## Project structure
```text
MetroFlow_Seoul/
├── backend/
│   ├── __init__.py
│   └── main.py
├── data/
│   └── seoul-metro-2015.logs.csv.gz
├── frontend/
│   ├── index.html
│   └── static/
│       ├── app.js
│       └── style.css
├── requirements.txt
└── README.md
```
