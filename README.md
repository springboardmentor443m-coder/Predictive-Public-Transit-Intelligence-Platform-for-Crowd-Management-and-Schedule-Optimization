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
