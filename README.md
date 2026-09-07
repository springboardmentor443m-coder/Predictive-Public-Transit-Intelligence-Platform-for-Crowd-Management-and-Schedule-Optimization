# MetroFlow: AI Platform for Metro Crowd Management & Scheduling

**MetroFlow** is an AI-powered public transit intelligence platform designed for metro operators to track passenger density in real time, predict crowd bottlenecks, and dynamically optimize train dispatch schedules.

---

## System Architecture

- **Backend:** Python 3.11+, FastAPI (modular routers, async SQLAlchemy, Pydantic v2 schemas, WebSockets).
- **Frontend:** Next.js 14 (App Router), React, TypeScript, Tailwind CSS, Lucide React, Recharts.
- **AI & Analytics Engine:**
  - **XGBoost / LightGBM:** 15-min, 30-min, 60-min horizon station demand forecasting.
  - **PyTorch LSTM & Random Forest:** Peak-hour congestion risk & anomaly prediction.
  - **Synthetic Transit Data Generator:** Simulates smart card turnstile taps across 16 stations (Red Line & Blue Line) with rush hour curves.
- **Databases & Caching:** PostgreSQL (Relational metadata), MongoDB (Motor event logs), Redis (Pub/Sub & station density cache) with automatic local SQLite & memory failover.

---

## Core Modules & Pages

1. **Executive Overview Dashboard (`/dashboard`)**: Key system KPIs (Active trains, system passenger count, critical stations, OTP rate) and interactive SVG Metro Network Telemetry Map.
2. **Live Crowd Monitoring (`/live-monitoring`)**: Interactive station grid with live platform density gauges and inflow/outflow passengers per minute (ppm) metrics.
3. **AI Forecast & Insights Page (`/predictions`)**: Multi-horizon demand forecast curves with 95% confidence bounds and automated frequency optimization suggestions (+2 trains/hr).
4. **Train Schedule & Dispatch Manager (`/schedules`)**: Timetable view of active train runs, delay propagation tracking, and headway override controls with safety checks (> 3 min headway).
5. **Alerts & Operations Center (`/alerts`)**: Threshold alert feed (Overcrowding > 80%, Train Delays) and one-click Public Address (PA) & SMS broadcast triggers.
6. **Analytics & Performance Reports (`/analytics`)**: 24-hour throughput trends, line OTP breakdown, and exportable CSV reports.

---

## Quick Start (Local Execution)

### 1. Backend Setup & ML Model Training
```bash
cd backend

# Install dependencies
pip install -r requirements.txt email-validator

# Train ML Models (XGBoost & PyTorch LSTM)
$env:PYTHONPATH="."
python app/ml/train_demand_model.py
python app/ml/train_crowd_model.py

# Run API Server & WebSocket Stream
uvicorn app.main:app --reload --port 8000
```
API Documentation: `http://localhost:8000/docs`

### 2. Frontend Setup
```bash
cd frontend

# Install Node dependencies
npm install

# Start Next.js Development Server
npm run dev
```
Access UI Dashboard: `http://localhost:3000`

---

## Docker Compose Orchestration

To launch the full containerized stack (FastAPI, Next.js, PostgreSQL, MongoDB, Redis):
```bash
docker-compose up --build
```

---

## Running Automated Tests

Run the backend test suite covering authentication, density calculations, ML predictions, and safety overrides:
```bash
cd backend
$env:PYTHONPATH="."
pytest tests
```
