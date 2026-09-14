# Predictive Public Transit Intelligence Platform

## Crowd Management and Schedule Optimization using NYC Subway Traffic 2017-21 Dataset

### Overview
This project analyzes the NYC Subway Traffic dataset (2017-2021) — hourly entry/exit data for 469 stations — to build a predictive platform for crowd management and schedule optimization.

### Features
- **Exploratory Data Analysis (EDA)**: Comprehensive statistical analysis and visualization
- **Weekly Traffic Pattern Analysis**: Hourly, daily, and weekly patterns across all stations
- **Crowd Prediction Model**: ML-based prediction of crowd levels using XGBoost/RandomForest
- **Schedule Optimization**: Optimal train frequency recommendations based on demand
- **Visualization Dashboard**: Heatmaps, trend charts, and comparison plots

### Dataset
- **Source**: [NYC Subway Traffic 2017-21 — hourly entry/exit for 469 stations](https://www.kaggle.com/datasets/eddeng/nyc-subway-traffic-data-20172021)
- **Period**: 2017-2021 (5 years of hourly data)
- **Stations**: 469 subway stations
- **Metrics**: Entries and exits per hour

### Project Structure
```
Predictive-Public-Transit-Intelligence-Platform-for-Crowd-Management-and-Schedule-Optimization/
├── data/                    # Dataset files
├── src/                     # Source code
│   ├── __init__.py
│   ├── main.py             # Main pipeline
│   ├── data_loader.py      # Data loading & preprocessing
│   ├── eda.py              # Exploratory data analysis
│   ├── weekly_analysis.py  # Weekly schedule analysis
│   ├── crowd_predictor.py  # ML crowd prediction
│   ├── schedule_optimizer.py # Schedule optimization
│   ├── visualization.py    # Visualization module
│   └── download_data.py    # Kaggle dataset downloader
├── notebooks/               # Jupyter notebooks
├── models/                  # Trained ML models
├── reports/                 # Generated reports
├── visualizations/          # Chart outputs
├── requirements.txt         # Python dependencies
└── README.md               # This file
```

### Quick Start

#### 1. Install Dependencies
```bash
pip install -r requirements.txt
```

#### 2. Download Dataset
```bash
# Place your Kaggle API token at ~/.kaggle/kaggle.json
python src/download_data.py
```

#### 3. Run Complete Pipeline
```bash
python src/main.py
```

#### 4. Run Individual Modules
```python
from src.data_loader import load_data, preprocess_data
from src.eda import generate_eda_report
from src.weekly_analysis import WeeklyScheduleAnalyzer
from src.crowd_predictor import CrowdPredictor
from src.schedule_optimizer import ScheduleOptimizer
```

### Weekly Schedule Output
The platform generates optimized weekly schedules with:
- **Peak hour identification** for each station
- **Train frequency recommendations** (Normal/High/Reduced)
- **Weekend vs weekday traffic comparison**
- **Resource allocation** based on traffic volume
- **Top 20 busiest stations ranking**

### Model Performance
The crowd prediction model uses ensemble methods (XGBoost, RandomForest, GradientBoosting) with:
- **R² Score**: Typically 0.85+
- **Features**: Hour, day of week, month, station ID, historical patterns
- **Output**: Predicted hourly entry/exit counts

### Visualization Gallery
| Chart | Description |
|-------|-------------|
| Weekly Heatmap | Hourly traffic by day of week |
| Station Ranking | Top 20 busiest stations |
| Monthly Trends | 5-year traffic trends |
| Weekday vs Weekend | Traffic pattern comparison |
| Predictions vs Actual | Model validation |

### Contributing
See [CONTRIBUTING.md](../README.md) for guidelines.

### License
MIT License

---

## 🚇 MetroFlow Live Platform (FastAPI + React) — NEW

Full operational app built on top of the analysis pipeline above, covering all
MetroFlow modules (auth/RBAC, crowd monitoring, scheduling, AI prediction,
alerts WS, analytics dashboards). Dataset choice documented in `data/README.md`:
**NYC Subway Traffic 2017–21** (hourly entries+exits, 469 stations) over Seoul
Metro Usage — the in/out split enables net-flow, density bands, and headway mapping.

### Run live platform (no Kaggle login needed)
```bash
# 1. sample NYC-style data
pip install pandas numpy
python data/generate_sample.py --stations 12 --days 90

# 2. backend (FastAPI :8000)
cd backend
pip install -r requirements.txt
python -m app.ml.train_model   # RandomForest R² ≈ 0.93, acc ≈ 90%
python -m app.db.seed
uvicorn app.main:app --reload --port 8000   # docs at /docs, login admin/admin123

# 3. frontend (new terminal, :5173 proxies /api → :8000)
cd frontend
npm install; npm run dev
```

### Docker
```bash
docker compose up --build
# frontend http://localhost:5173 | backend http://localhost:8000/docs
```

### API map
| Module | Endpoints |
|---|---|
| Auth/users | POST /api/auth/register, POST /api/auth/login, GET /api/auth/me (JWT, admin/operator/viewer) |
| Crowd | GET /api/stations, /api/crowd/current, /history, /heatmap, /inflow-outflow |
| Scheduling | GET/POST /api/schedules, POST /api/schedules/{id}/delay, GET /api/schedules/optimize |
| AI prediction | GET /api/predictions/crowd, /demand, /peak-hours, /recommendations |
| Alerts | GET/POST /api/alerts, POST /api/alerts/{id}/ack, WS /api/alerts/ws/alerts |
| Analytics | GET /api/analytics/traffic, /station-performance, /operational, /kpis |

### Verified
- Backend TestClient: auth → stations(12) → heatmap → 5h forecast → optimize → kpis → alert post — ALL PASSED
- ML: MAE ≈ 238 pax, R² ≈ 0.927 on 25,920-row sample; peak 8am ≈ 4,897 pax/hr
- Frontend: `vite build` clean; pages: Overview, Crowd, Scheduling, Predictions, Alerts, Analytics
