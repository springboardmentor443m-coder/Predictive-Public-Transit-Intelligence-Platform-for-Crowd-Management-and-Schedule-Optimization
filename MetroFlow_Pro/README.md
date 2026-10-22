# MetroFlow Pro
A full local prototype for station crowd forecasting and schedule-aware train monitoring.

## Features
- 30 stations with generated passenger entry/exit data.
- `HistGradientBoostingRegressor` for station demand forecasts.
- `HistGradientBoostingClassifier` for train delay-risk classification.
- Train board with train ID, line, station, scheduled time, simulated actual time, delay and status.
- Capacity-based crowd index, scenario simulator, alerts with acknowledge action, and FastAPI docs.
- Dashboard served by FastAPI; no npm install required.

**Data honesty:** All data is generated/synthetic, not an official or live metro feed. A delay alert references a train record with a scheduled time and a simulated actual time. Crowd percentages are a capacity proxy, not a physical passenger count.

## Run on Windows (Python 3.10–3.12 recommended)
```powershell
py -3.12 -m venv .venv
.\.venv\Scripts\Activate.ps1
python -m pip install --upgrade pip
pip install -r requirements.txt
python -m uvicorn app.main:app --reload --port 8000
```
Open http://127.0.0.1:8000/dashboard and API docs at http://127.0.0.1:8000/docs.
If activation is blocked: `Set-ExecutionPolicy -Scope Process -ExecutionPolicy Bypass`, then activate again.

Tests: `pip install -r requirements-dev.txt` then `pytest -q`.

## API
`GET /api/overview`, `/api/stations`, `/api/trains`, `/api/alerts`, `/api/forecast/{station_id}?horizon_hours=6`
`POST /api/simulation/start`, `/api/simulation/stop`, `/api/simulation/tick` with `{"scenario":"rush_hour"}`, `POST /api/alerts/{id}/ack`, `POST /api/ai/train`.
