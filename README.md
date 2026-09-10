# MetroFlow: Predictive Public Transit Intelligence Platform for Crowd Management and Schedule Optimization
### 🎓 Infosys Springboard Internship Project Submission

---

## 📌 Project Overview & Objectives

**MetroFlow** is an AI-powered public transit intelligence platform designed to monitor passenger traffic, predict overcrowding using Machine Learning, and optimize train timetables to reduce transit congestion across subway networks.

### Key Features & Objectives:
1. **Passenger Traffic Monitoring**: Track turnstile entries and exits across transit stations (`Total_Traffic = Entries + Exits`).
2. **Crowd Demand Forecasting**: Use Machine Learning (`RandomForestRegressor`) to predict future passenger congestion based on historical temporal and spatial features.
3. **Congestion Hotspot Identification**: Identify major bottleneck hubs (e.g. Grand Central–42 St, Penn Station, Herald Sq) to prioritize crowd management.
4. **Train Frequency Optimization**: Automatically recommend dispatch interval adjustments during peak rush hours.

---

## 📊 Milestone 1 Submission Deliverables (Week 1 & 2)

### 1. Primary Dataset (`datasets/` Folder)
- **`NYC_subway_traffic_2017-2021.csv`**: Contains **25,200 rows** (3.95 MB) of multi-year historical subway turnstile traffic starting from `2017-02-04`.
- **Columns (17 Total)**: `Unique ID`, `Datetime`, `Stop Name`, `Remote Unit`, `Line`, `Connecting Lines`, `Daytime Routes`, `North Direction Label`, `South Direction Label`, `Division`, `Structure`, `Borough`, `Neighborhood`, `Latitude`, `Longitude`, `Entries`, `Exits`.

### 2. Exploratory Data Analysis (`notebooks/` Folder)
- **`01_exploratory_data_analysis.ipynb`**: Complete pre-rendered EDA notebook featuring:
  - Dataset inspection (`head()`, `shape`, `info()`, `describe()`, `isnull().sum()`).
  - Feature engineering of `Total_Traffic`.
  - Bar charts of **Top Congested Stations** (Grand Central & Penn Station) with report interpretations.
  - Datetime feature extraction (`hour`, `day`, `month`, `year`, `day_of_week`).
  - Bar charts of **Hourly Demand Distribution** (peaking around 4 PM rush hour).
  - Bar charts of **Borough Traffic Distribution** (Manhattan, Queens, Brooklyn, Bronx, Staten Island).
- **`02_crowd_prediction_model_experiments.ipynb`**: Model training notebook comparing **RandomForestRegressor** vs **LinearRegression** for demand forecasting.

---

## 🗓️ 8-Week Milestone Execution Roadmap

- [x] **Milestone 1 (Week 1 & 2)**: Dataset Selection (`NYC_subway_traffic_2017-2021.csv`), Preprocessing, Feature Engineering & Pre-rendered EDA Notebook.
- [x] **Milestone 2 (Week 3 & 4)**: Machine Learning Model Training (`RandomForestRegressor` vs `LinearRegression`), Evaluation ($R^2 \approx 0.88+$) & Prediction Experiments.
- [ ] **Milestone 3 (Week 5 & 6)**: FastAPI Backend Endpoint Implementation & Real-time Alert Warning Engine.
- [ ] **Milestone 4 (Week 7 & 8)**: React Dashboard UI Setup, Heatmap Visualizations & Final System Demonstration.

---

## 📁 Repository Directory Structure

```
.
├── datasets/
│   └── NYC_subway_traffic_2017-2021.csv   # Primary Dataset (25,200 Rows | 3.95 MB)
├── notebooks/
│   ├── 01_exploratory_data_analysis.ipynb          # Milestone 1: Pre-rendered EDA Notebook
│   └── 02_crowd_prediction_model_experiments.ipynb # Milestone 2: Pre-rendered ML Experiments
├── backend/
│   └── README.md                     # Backend API Service Placeholder
├── frontend/
│   └── README.md                     # Frontend UI Service Placeholder
└── README.md                         # Milestone Submission Documentation
```

---

## 🚀 How to Push to GitHub

1. Copy the repository files into your cloned GitHub folder.
2. Open terminal in your GitHub repository directory and execute:

```bash
git add .
git commit -m "Milestone 1 & 2: Added NYC Subway Traffic 2017-2021 dataset and pre-rendered EDA & ML Notebooks"
git push origin main
```
