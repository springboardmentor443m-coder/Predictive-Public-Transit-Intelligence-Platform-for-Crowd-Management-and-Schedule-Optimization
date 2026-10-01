# MetroFlow – AI Public Transit Intelligent Platform

> Real-time AI-powered crowd analytics for **Bengaluru Metro** using 92,280 historical records.

## 🚀 Quick Start

### 1. Backend (FastAPI)
```bash
cd backend
.venv\Scripts\uvicorn main:app --host 0.0.0.0 --port 8000 --reload
```
API Docs: http://localhost:8000/docs

### 2. Frontend (Next.js)
```bash
cd frontend
npm run dev
```
Dashboard: http://localhost:3000

---

## 🧠 Platform Features

| Feature | Description |
|---|---|
| **Live Ridership** | Simulated real-time ridership across 83 stations (±15% from historical avg) |
| **Network Daily Chart** | Total daily ridership trend (Aug–Sep 2025) |
| **Hourly Profile** | Average ridership by hour (color-coded by load) |
| **Line Comparison** | Purple Line vs Green Line hourly comparison |
| **AI 24-Hour Forecast** | Weighted moving average prediction for next 24h |
| **Top 10 Stations** | Busiest stations by average ridership |
| **Station Deep-Dive** | Per-station: hourly pattern, weekday pattern, AI 6-hour prediction |
| **Anomaly Detection** | Z-score based surge/drop detection |
| **AI Insights** | 4 generated intelligence insights from data patterns |
| **Status Distribution** | Pie chart of low/moderate/high/critical stations |

---

## 📁 Project Structure

```
MetroFlow/
├── backend/
│   ├── main.py                      # FastAPI app entry point
│   └── app/
│       ├── database.py              # SQLAlchemy + PostgreSQL
│       ├── models/station.py        # Station ORM model
│       ├── schemas/station.py       # Pydantic schemas
│       ├── routes/
│       │   ├── station.py           # CRUD station routes
│       │   └── analytics.py        # All AI analytics routes
│       └── services/
│           └── analytics.py        # Core AI analytics engine
├── datasets/
│   └── raw/raw/station-hourly.csv  # Bengaluru Metro dataset (92,280 records)
└── frontend/
    ├── app/
    │   ├── page.tsx                 # Main dashboard (7 chart types)
    │   ├── layout.tsx               # App layout
    │   ├── globals.css              # Dark theme + animations
    │   └── lib/api.ts              # Backend API client
    └── .env.local                   # API URL config
```

---

## 📊 Dataset

- **Source**: Bengaluru Metro Station-Hourly Ridership
- **Period**: Aug 1 – Sep 30, 2025
- **Records**: 92,280
- **Stations**: 83 unique stations
- **Fields**: Date, Hour, Station, Ridership

## 🔌 Key API Endpoints

| Endpoint | Description |
|---|---|
| `GET /analytics/live` | Live ridership (simulated) |
| `GET /analytics/network/daily` | Daily total ridership |
| `GET /analytics/network/hourly` | Hourly profile |
| `GET /analytics/network/top-stations` | Top N busiest stations |
| `GET /analytics/network/line-comparison` | Purple vs Green line |
| `GET /analytics/stations/{name}/hourly` | Per-station hourly avg |
| `GET /analytics/stations/{name}/weekday` | Day-of-week pattern |
| `GET /analytics/stations/{name}/predict` | AI predictions |
| `GET /analytics/ai/insights` | AI-generated insights |
| `GET /analytics/ai/anomalies` | Anomaly detection |
| `GET /analytics/ai/forecast` | 24h network forecast |
| `GET /analytics/ai/peak-analysis` | Peak hour analysis |
