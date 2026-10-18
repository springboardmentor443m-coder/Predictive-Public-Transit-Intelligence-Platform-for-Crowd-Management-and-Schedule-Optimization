# 🚇 MetroFlow: Predictive Transit Intelligence & Decision Support Platform
> **AI-Powered Crowd Management, Demand Forecasting & Dynamic Headway Advisory for Namma Metro (BMRCL Bengaluru)**

[![RTI Records](https://img.shields.io/badge/RTI_Records-92%2C280_Verified-brightgreen.svg)](#actual-bmrcl-datasets)
[![XGBoost Accuracy](https://img.shields.io/badge/XGBoost_R%C2%B2-0.936-blue.svg)](#ml-architecture--results)
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](LICENSE)

MetroFlow is an enterprise transit intelligence system engineered for Namma Metro (BMRCL Bengaluru). Operating on genuine GTFS network topology and official source RTI hourly ridership observations (August & September 2025 across 83 stations), MetroFlow enables verifiable demand forecasting, unsupervised crowd anomaly detection, and dynamic headway recommendations.

---

## 👥 Project Overview & Migration

MetroFlow has undergone a complete pivot away from synthetic simulations:
* **From:** Simulated Hyderabad Metro (HMRL) transit models with synthetic card taps.
* **To:** Genuine BMRCL (Bengaluru) operations powered exclusively by real historical RTI datasets.

### System Capabilities
* **Full-Network BMRCL GTFS:** 83 stations spanning the Purple Line (*Challaghatta ⇄ Whitefield Kadugodi*) and Green Line (*Madavara ⇄ Silk Institute*), centered at Nadaprabhu Kempegowda Station Majestic (KGWA) interchange.
* **Historical Replay Telemetry:** Replays authentic hourly data across August and September 2025 without synthetic noise or fabricated pedestrian models.
* **Leakage-Free Demand Forecasting:** XGBoost models projecting future passenger flows (+1h, +2h, and +4h) built on strict chronological splits.
* **Unsupervised Isolation Forest:** Detects abnormal demand surges and platform congestion bottlenecks.
* **Dynamic Crowd Classification:** Platform occupancy rates derived from real BMRCL ridership relative to station capacities (**NORMAL** <60%, **MODERATE** 60%–79%, **CRITICAL** ≥80%).
* **Headway Optimization:** Decision support engine for frequency adjustments maintaining a safety buffer of ≥ 3 minutes.

---

## 📗 Actual BMRCL Datasets

The system runs strictly on verified, authentic datasets in `/data`:

| File | Size | Description | Authoritative Source |
| :--- | :--- | :--- | :--- |
| `bmrcl_gtfs.zip` | 823 KB | 83 Stations, 2 Corridors, 2,800+ scheduled trips | Community-built GTFS (OSM & Published Timetables) |
| `bmrcl_entry_exit_august_2025.xlsx` | 231 KB | 32,520 Hourly Entry records (18 business days) | Official BMRCL RTI Disclosure |
| `bmrcl_entry_exit_september_2025.xlsx` | 682 KB | 59,760 Hourly Entry & Exit records (30 full days) | Official BMRCL RTI Disclosure |
| `bmrcl_station_codes.csv` | 2.5 KB | 70 Official BMRCL short station codes | BMRCL Reference Nomenclature |

* **Ingested Rows in SQLite `metroflow.db`:** 92,280 rows
* **Master Cleaned Parquet Records:** 91,782 rows
* **Synthetic / HMRL Data Detected:** 0 (strictly purged)

---

## 🔄 Across-Station Reconciliation

The automated ingestion pipeline (`backend/app/datasets/bmrcl_pipeline.py`) executes a 5-Tier Reconciliation Engine:

1. **Tier 1 (Exact Station Code):** Direct identifier matching.
2. **Tier 2 (Code Lookup):** Cross-referenced against `bmrcl_station_codes.csv`.
3. **Tier 3 (Normalized Match):** Stripping numeric prefixes (e.g., `11-Baiyappanahalli` → `baiyappanahalli`) and punctuation.
4. **Tier 4 (Aliases & Historical Names):** Majestic / Kempegowda → KGWA, KR Train Station → BRCS, Yeshwanthpur Industry → YPI, etc.
5. **Tier 5 (Conservative Fuzzy):** SequenceMatcher with rigid score threshold (≥ 0.85).

* **Resolution Ratio:** 84 / 84 stations resolved (100%), 0 unmatched.

---

## 🧠 ML Architecture & Results

Trained exclusively on point-in-time features to prevent leakage:
`station_id`, `hour`, `day_of_week`, `is_weekend`, `lag_1h`, `lag_2h`, `rolling_mean_3h`, `rolling_max_3h`.

| Model Horizon | MAE | RMSE | R² Score | Baseline Persistence MAE | Baseline R² |
| :--- | :--- | :--- | :--- | :--- | :--- |
| **Horizon +1h** | 69.29 pax/hr | 173.08 | 0.936 | 222.60 pax/hr | 0.337 |
| **Horizon +2h** | 85.00 pax/hr | 209.67 | 0.907 | — | — |
| **Horizon +4h** | 98.51 pax/hr | 238.16 | 0.880 | — | — |

---

## 💨 Quick Start

### 1. Backend Setup
```powershell
cd backend
python -m venv venv
.\venv\Scripts\Activate.ps1
pip install -r requirements.txt
python -m app.datasets.bmrcl_pipeline
python app/ml/train_bmrcl_models.py
python -m uvicorn app.main:app --host 127.0.0.1 --port 8000 --reload
