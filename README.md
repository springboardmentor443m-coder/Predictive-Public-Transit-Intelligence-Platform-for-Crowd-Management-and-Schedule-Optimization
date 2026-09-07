# MetroFlow: AI Public Transit Intelligence Platform

An intelligent public transit operations platform designed to monitor passenger density across stations, forecast commuter surges using machine learning, and dynamically adjust train dispatch schedules to relieve network bottlenecks.

---

## Deliverables Summary

### Milestone 1: Data Pipeline & Crowd Monitoring
* **Operator Authentication**: Secure credential validation for transit operations via `/api/v1/auth/login`.
* **Turnstile Ingestion**: Automated pipeline processing turnstile entries and exits to calculate net station accumulation and classify congestion levels (`NORMAL`, `MODERATE`, `HIGH`, `CRITICAL`).
* **Real-Time Operations Dashboard**: Web dashboard featuring dynamic passenger flow charts, live station status tables, and high-density alerts.

### Milestone 2: Dynamic Scheduling & ML Demand Forecasting
* **Active Timetable Management**: Endpoint at `/api/v1/scheduling/timetable` calculating route delays, line occupancy rates, and dispatch timelines.
* **Dynamic Headway Optimization**: Headway compression algorithm dynamically reducing train intervals from 8 minutes to 3–5 minutes during peak surges.
* **Peak-Hour Capacity Buffering**: Rush-hour demand policies scaling capacity multipliers ($1.45\times - 1.50\times$) during morning and evening windows.
* **ML Passenger Demand Forecasting**: Trained Random Forest Regressor predicting station passenger volume based on temporal variables (hour, day of week).
* **Corridor Volatility Classification**: Categorization engine identifying high-variance central transit hubs versus low-variance residential feeders.
* **Operational Decision Engine**: Automated rule-based system generating prioritized operational recommendations (platform metering, auxiliary train injection).

---

## Directory Architecture

```text
Virtual Internship/
├── backend/
│   ├── app/
│   │   └── main.py                   # FastAPI application & route endpoints
│   ├── data/
│   │   ├── live_crowd_summary.csv    # Processed station accumulation metrics
│   │   ├── active_schedules.csv      # Processed route schedules & delay metrics
│   │   └── traffic_patterns.csv      # Station volatility classifications
│   ├── models/
│   │   └── demand_forecast_model.pkl # Trained Random Forest model artifact
│   ├── clean_and_sync_data.py        # Dataset preprocessing and validation pipeline
│   ├── train_clean_model.py          # ML training and evaluation script
│   ├── schedule_manager.py           # Timetable aggregation module
│   ├── frequency_adjuster.py         # Dynamic headway adjustment engine
│   ├── peak_optimizer.py             # Rush-hour buffer optimization logic
│   ├── traffic_pattern_analyzer.py   # Corridor variance classification
│   ├── traffic_reporter.py           # Performance metrics JSON digest generator
│   ├── ai_recommender.py             # Operational recommendations engine
│   └── test_milestone2.py            # Automated endpoint testing script
├── frontend/
│   └── index.html                    # Operations dashboard UI (Tailwind CSS + Chart.js)
├── .gitignore                        # Git exclusion rules (virtual environments, raw CSVs)
└── README.md                         # Project documentation