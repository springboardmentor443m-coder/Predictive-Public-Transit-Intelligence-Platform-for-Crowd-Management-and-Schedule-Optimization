# MetroFlow: AI Public Transit Intelligence Platform for Crowd Management and Schedule Optimization

MetroFlow is an AI-powered smart transit operations and crowd management platform designed to monitor passenger density across stations, forecast commuter surges using machine learning, and dynamically optimize train dispatch schedules to relieve network bottlenecks without relying on computer vision.

---

## Directory Architecture

```text
Virtual Internship/
├── backend/
│   ├── app/
│   │   └── main.py                     # FastAPI application, route definitions, and CORS middleware
│   ├── data/
│   │   ├── live_crowd_summary.csv      # Real-time station footfall & congestion level metrics
│   │   ├── active_schedules.csv        # Timetables, delay metrics, and headway records
│   │   ├── traffic_patterns.csv        # Corridor variance classifications
│   │   ├── alerts_history.csv          # Persistent alert and notification logs
│   │   ├── frequency_recommendations.csv # AI-recommended headway adjustments
│   │   ├── peak_hour_policy.csv        # Surge capacity multiplier configuration
│   │   └── traffic_analysis_report.json # Historical throughput and volatility digest
│   ├── models/
│   │   └── demand_forecast_model.pkl   # Serialized Random Forest demand regressor
│   ├── alert_manager.py                # Rule-based threshold alerts & emergency broadcast service
│   ├── analytics_engine.py             # Network KPI aggregation & congestion heatmap engine
│   ├── simulator.py                    # Live background telemetry sensor & drift simulator
│   ├── clean_and_sync_data.py          # Data ingestion and cleaning pipeline
│   ├── train_clean_model.py            # Model training and artifact serialization
│   ├── schedule_manager.py             # Active dispatch timetable manager
│   ├── frequency_adjuster.py           # Dynamic headway compression algorithm
│   ├── peak_optimizer.py               # Rush-hour buffer scaling logic
│   ├── traffic_pattern_analyzer.py     # Corridor variance classification
│   ├── test_milestone2.py              # Milestone 2 validation suite
│   ├── test_milestone3.py              # Milestone 3 alert and analytics validation suite
│   ├── test_full_system.py             # End-to-end multi-milestone integration test suite
│   ├── Dockerfile                      # Backend container specification
│   └── requirements.txt                # Python package dependencies
├── frontend/
│   └── index.html                      # Multi-view SPA command console (Tailwind CSS, Chart.js)
├── docker-compose.yml                  # Multi-container orchestration definition
├── .gitignore                          # Repository exclusion rules (raw data, virtual environments)
└── README.md                           # Platform documentation