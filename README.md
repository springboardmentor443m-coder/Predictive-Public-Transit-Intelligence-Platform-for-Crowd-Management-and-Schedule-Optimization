# MetroFlow Seoul

**Predictive Public Transit Intelligence Platform for Crowd Management and Schedule Optimization**

A student-friendly full-stack dashboard built with **Python, FastAPI, HTML, CSS, and JavaScript**. This project does not use Streamlit.

## Features

- **Overview dashboard:** passenger entries/exits, total flow, and historical trends.
- **Auto-starting live simulator:** replays historical records every 1.8 seconds to demonstrate a changing operations feed. The overview and alerts auto-refresh every 30 seconds while the page is open.
- **Forecast & schedules:** hour-of-day historical-average baseline for upcoming hours.
- **Crowd heatmap:** observed flow patterns by station and hour.
- **Alerts center:** illustrative high-flow alerts and demo announcement composer.
- **Analytics:** station comparisons, hourly averages, and CSV export.

## Dataset and scope

- The dashboard analyzes **20 station codes** for performance.
- The current processed view contains approximately **146,000 records**.
- The bundled compressed source file is `data/seoul-metro-2015.logs.csv.gz`.
- Source data columns: `timestamp`, `station_code`, `people_in`, `people_out`.
- Source data period: 2015-01-01 to 2016-01-01 (Asia/Seoul).

Station codes are used as identifiers; no unverified station-name mapping is assumed.

## Run on Windows

1. Download and extract this project ZIP.
2. Install Python 3.10 or newer.
3. Open Command Prompt or PowerShell in the extracted `MetroFlow_Seoul` folder.
4. Run:

   ```powershell
   python -m venv .venv
   .venv\Scripts\activate
   pip install -r requirements.txt
   python -m uvicorn backend.main:app --reload
   ```

5. Open **http://127.0.0.1:8000** in your browser.
6. Optional API documentation: **http://127.0.0.1:8000/docs**.

If PowerShell blocks virtual-environment activation, you can run `pip install -r requirements.txt` and then `python -m uvicorn backend.main:app --reload` from the project folder.

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
├── .gitignore
└── README.md
```

## Important limitations

The included data is historical, **not a live 2026 Seoul Metro feed**. The simulator automatically replays historical records; it does not connect to live Seoul Metro operations. The 30-second dashboard refresh updates historical summaries and alerts, not current real-world passenger counts. Forecasts use a simple historical-average baseline and are not validated production predictions. Alerts are illustrative and do not represent official capacity thresholds. Demo announcements are not broadcast to passengers.
