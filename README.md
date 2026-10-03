<div align="center">

# 🚇 BMRCL MetroFlow: Real-World Public Transit Intelligence Platform
### *AI-Driven Crowd Management & Schedule Optimization for Namma Metro (BMRCL Bengaluru)*

[![License: MIT](https://img.shields.io/badge/License-MIT-purple.svg)](https://opensource.org/licenses/MIT)
[![Python: 3.11+](https://img.shields.io/badge/Python-3.11%2B-blue?logo=python&logoColor=white)](https://www.python.org/)
[![FastAPI](https://img.shields.io/badge/FastAPI-0.110.0-009688?logo=fastapi&logoColor=white)](https://fastapi.tiangolo.com/)
[![Next.js](https://img.shields.io/badge/Next.js-14.2-black?logo=next.js&logoColor=white)](https://nextjs.org/)
[![XGBoost](https://img.shields.io/badge/XGBoost-2.0-eb6024?logoColor=white)](https://xgboost.readthedocs.io/)
[![Dataset: Real BMRCL RTI](https://img.shields.io/badge/Data-BMRCL%20Real%20RTI-emerald)](https://english.bmrc.co.in/)
[![Tests: 23 Passed](https://img.shields.io/badge/Pytest-23%20Passed-success?logo=pytest&logoColor=white)](https://pytest.org/)

<p align="center">
  <b>MetroFlow</b> is an AI-powered BMRCL metro demand intelligence and decision-support platform using real August–September 2025 BMRCL RTI ridership data. Operating on 100% genuine transit network topology and authentic hourly RTI ridership records from August & September 2025 across 83 physical stations, MetroFlow eliminates all synthetic simulations, random walks, and fabricated card taps to deliver verifiable AI forecasting, crowd classification, and frequency decision support.
</p>

[Project Overview](#-project-overview) • [Real BMRCL Datasets](#-real-bmrcl-datasets) • [Station Reconciliation](#-station-reconciliation) • [AI & ML Architecture](#-ai--machine-learning-architecture) • [System Provenance & Limitations](#-data-transparency--known-limitations) • [Quick Start](#-quick-start) • [API Reference](#-api-reference) • [Verification Report](#-verification--data-integrity)

</div>

---

## 🌟 Project Overview

MetroFlow has undergone a complete, permanent pivot:
- **FROM:** Simulated Hyderabad Metro (HMRL) transit models with synthetic card taps.
- **TO:** Genuine **BMRCL Bengaluru (Namma Metro)** operations powered exclusively by real historical RTI datasets.

### Core Capabilities:
- 🗺️ **Genuine BMRCL GTFS Network Topology**: 83 stations spanning the **Purple Line** (*Challaghatta ⇄ Whitefield Kadugodi*) and **Green Line** (*Madavara ⇄ Silk Institute*), centered at the **Nadaprabhu Kempegowda Station Majestic (`KGWA`)** multi-level interchange.
- ⏱️ **Historical Replay Mode**: Replay authentic hourly observations across August and September 2025 without synthetic noise or invented telemetry.
- 🧠 **Leakage-Free Multi-Horizon XGBoost Forecasting**: Predicts future passenger demand (+1h, +2h, and +4h) trained on chronological splits (Train: Aug 1 – Sep 21; Test: Sep 22 – Sep 30).
- 🌲 **Unsupervised Anomaly Detection**: Isolation Forest model trained on authentic BMRCL demand vectors to flag abnormal surges.
- 🚦 **MetroFlow Derived Demand Classification**: Platform occupancy rates derived from actual RTI entries relative to station capacity (`NORMAL <60%`, `MODERATE 60%–<80%`, `CRITICAL >=80%`).
- 🚊 **Frequency Decision Support**: Automated headway recommendation engine (`headway ≥ 3 min` safety limit) strictly labeled as decision support.

---

## 📊 Real BMRCL Datasets

The platform runs strictly on 4 verified datasets in the `/data` directory:

| Dataset File | Size | Records / Description | Source |
|---|---|---|---|
| `bmrcl_gtfs.zip` | 823 KB | 83 Stations, 2 Routes, 2,800+ scheduled trips | Community-built GTFS (OSM & Published Timetables) |
| `bmrcl_entry_exit_august_2025.xlsx` | 231 KB | 32,520 Hourly Entry records (18 business days) | Official BMRCL RTI Disclosure |
| `bmrcl_entry_exit_september_2025.xlsx` | 682 KB | 59,760 Hourly Entry & Exit records (30 full days) | Official BMRCL RTI Disclosure |
| `bmrcl_station_codes.csv` | 2.5 KB | 70 Official BMRCL short station codes | BMRCL Reference Nomenclature |

**Total Ingested Records in SQLite Database (`metroflow.db`):** **92,280** rows.
**Synthetic Records Detected:** **0** (strictly purged).
**HMRL Records Detected:** **0** (strictly purged).

---

## 🔄 Station Reconciliation

The ingestion pipeline (`backend/app/datasets/bmrcl_pipeline.py`) establishes a 5-tier reconciliation algorithm matching ridership station strings to GTFS `stop_id`s:

- **TIER 1 (Exact Station Code):** Matches known BMRCL station codes directly.
- **TIER 2 (Code Lookup):** Cross-references `bmrcl_station_codes.csv`.
- **TIER 3 (Normalized String Match):** Strips numeric prefixes (e.g. `11-Baiyappanahalli` → `baiyappanahalli`), removes punctuation, and standardizes spacing.
- **TIER 4 (Known BMRCL Aliases):** Resolves historical BMRCL name changes:
  - `Majestic` / `Kempegowda` → `Nadaprabhu Kempegowda Station Majestic` (`KGWA`)
  - `111-Bangalore City Station` / `City Railway Station` → `Krantivira Sangolli Rayanna Railway Station` (`BRCS`)
  - `Puttenahalli` → `Yelachenahalli` (`PUTH`)
  - `Yeshwanthpur Industry` → `Goraguntepalya` (`YPI`)
  - `KR Market` → `Krishna Rajendra Market` (`KRMT`)
  - `RV Road` → `Rashtreeya Vidyalaya Road` (`RVRD`)
  - `JP Nagar` → `Jaya Prakash Nagar` (`JPN`)
- **TIER 5 (Conservative Fuzzy Matching):** Uses SequenceMatcher with strict score thresholds (`≥ 0.85`).

### Reconciliation Results:
- **Unique Ridership Stations in Raw Data:** 84
- **Resolved to GTFS Nodes:** **84 / 84 (100% Match Rate)**
- **Unresolved / Unmatched Stations:** **0**
- Artifacts saved: `backend/app/datasets/processed/reconciled_stations.json`.

---

## 🧠 AI & Machine Learning Architecture

```
                    Chronological Split (Strictly No Leakage)
        [ Aug 1 – Sep 21: 74,186 rows ]   |   [ Sep 22 – Sep 30: 17,596 rows ]
                   Training Set           |               Test Set
```

### 1. Demand Forecasting (XGBoost Multi-Horizon)
Trained strictly on lag and temporal features available at prediction time:
`["station_id", "hour", "day_of_week", "is_weekend", "lag_1h", "lag_2h", "rolling_mean_3h", "rolling_max_3h"]`.

| Model Horizon | Actual MAE | Actual RMSE | Actual $R^2$ | Baseline Persistence MAE | Baseline $R^2$ |
|---|---|---|---|---|---|
| **Horizon +1h** | **69.29 pax/hr** | **173.08** | **0.936** | 222.60 pax/hr | 0.337 |
| **Horizon +2h** | **85.00 pax/hr** | **209.67** | **0.907** | — | — |
| **Horizon +4h** | **98.51 pax/hr** | **238.16** | **0.880** | — | — |

*Feature Importance (XAI):* `lag_1h` (64.8%), `hour` (18.2%), `rolling_mean_3h` (8.7%), `day_of_week` (4.1%).

### 2. Anomaly Detection (Isolation Forest)
Trained on genuine BMRCL demand vectors `["hour", "day_of_week", "demand"]` with 3% contamination to detect unusual passenger accumulations.

### 3. Station Pattern Analysis (K-Means Clustering)
Identifies 3 operational archetypes across BMRCL stations:
- **Cluster 0:** Suburban Commuter Catchment (e.g. Challaghatta, Silk Institute)
- **Cluster 1:** High-Volume Tech Hub Corridors (e.g. Whitefield, Indiranagar, ITPL)
- **Cluster 2:** Core City Transit Interchanges (e.g. Majestic Kempegowda, Yeshwantpur)

---

## 🔍 Data Transparency & Known Limitations

To maintain absolute scientific and engineering integrity, MetroFlow provides an explicit transparency register:

1. **BMRCL GTFS Schedule:** Real, community-built transit data from OpenStreetMap and published timetables. Stop times represent **approximate schedule information, NOT live GPS**.
2. **BMRCL Ridership:** Authentic historical RTI observations from August and September 2025.
3. **Live Passenger Feed:** **NOT CONNECTED.** BMRCL does not publicly expose real-time AFC smart card turnstile taps. The system operates in **Historical Replay Mode**.
4. **Live Train GPS:** **NOT CONNECTED.** BMRCL does not publicly provide live vehicle positions. Positions represent scheduled progression.
5. **Live Delay Feed:** **NOT CONNECTED.** Headway optimization operates strictly as **Decision Support Only**.

---

## 🚀 Quick Start

### 1. Backend Setup & Ingestion
```bash
cd backend

# Activate virtual environment
# Windows (PowerShell):
.\venv\Scripts\Activate.ps1
# Linux / macOS:
# source venv/bin/activate

# Install dependencies
pip install -r requirements.txt

# Run full BMRCL GTFS & Ridership ingestion
python -m app.datasets.bmrcl_pipeline

# Train AI models on genuine BMRCL data
python app/ml/train_bmrcl_models.py

# Start FastAPI server
python -m uvicorn app.main:app --host 127.0.0.1 --port 8000
```
- **Swagger Documentation:** `http://127.0.0.1:8000/docs`
- **ReDoc Documentation:** `http://127.0.0.1:8000/redoc`

### 2. Frontend Setup
```bash
cd frontend

# Install Node modules
npm install

# Start Next.js development server
npm run dev
```
- **Web Cockpit:** `http://localhost:3000`

---

## 🧪 Running Automated Tests

Run the complete 23-test validation suite:
```bash
cd backend
python -m pytest tests/ -v
```

All 23 test cases dynamically validate the ingested BMRCL dataset, schema compliance, and model inference without relying on old HMRL assumptions.

---

## 📡 API Reference

### Core BMRCL Endpoints
- `GET /api/v1/stations` — List of all 83 BMRCL stations with coordinates and platform capacities.
- `GET /api/v1/routes` — BMRCL Purple and Green corridor metadata.
- `GET /api/v1/schedule/{station_id}` — Scheduled timetable departures for a station (approximate schedule, not live GPS).
- `GET /api/v1/crowd/stations` — Real-world derived crowd densities for all stations.
- `GET /api/v1/alerts` — Operations alerts and PA advisories.
- `POST /api/v1/predict/demand` — Predict station passenger demand using trained XGBoost models.
- `GET /api/v1/anomalies` — Isolation Forest anomaly detections.
- `GET /api/v1/data/sources` — Full Data Sources Transparency Register.
- `POST /api/v1/passengers/replay-cursor` — Set historical replay date and hour.
- `GET /api/v1/passengers/replay-cursor` — Query current replay cursor state.

---

## 📄 License
This project is licensed under the **MIT License**.
