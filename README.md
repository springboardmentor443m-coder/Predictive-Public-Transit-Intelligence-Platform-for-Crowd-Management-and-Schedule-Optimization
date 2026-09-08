# MetroFlow: AI Platform for Metro Crowd Management and Scheduling
### 🎓 Infosys Springboard Project — Milestone 1 Submission (Week 1 & 2)

---

## 📌 Project Overview & Objectives

**MetroFlow** is an AI-powered metro crowd management and train scheduling platform. It helps metro authorities monitor real-time passenger density across platforms, predict overcrowding using Machine Learning, and optimize train timetables to reduce peak-hour congestion.

### Key Objectives:
1. **Real-time Crowd Monitoring**: Track passenger inflow/outflow across metro stations using ticketing & turnstile data.
2. **AI Passenger Demand Forecasting**: Use Machine Learning (`scikit-learn`) to predict future crowd surges.
3. **Train Schedule Optimization**: Dynamically adjust train frequencies during rush hours to prevent dangerous overcrowding.
4. **Emergency Alerts & Analytics**: Trigger automatic warnings when station capacity exceeds safe thresholds (>85%).

> **Note**: The system does **not** use computer vision or CCTV cameras. It uses numerical transportation data (turnstile entries/exits, station footfall logs, and train timetables).

---

## 📊 Milestone 1 Submission Deliverables (Week 1 & 2)

### 1. Selected Datasets (`datasets/` Folder)
- **`metro_ridership_dataset.csv`**: Contains 3,060 time-series passenger records logging entry counts, exit counts, live occupancy, and congestion levels across metro stations.
- **`train_schedules_dataset.csv`**: Operational train fleet logs (12 active trains across Red, Blue, Green, Yellow, and Purple lines).
- **`station_master_dataset.csv`**: Station directory metadata and capacity limits for 6 major metro hubs.

### 2. Exploratory Data Analysis (`notebooks/` Folder)
- **`01_exploratory_data_analysis.ipynb`**: Analyzes passenger arrival patterns, hourly occupancy curves, and station congestion bottlenecks.
- **`02_crowd_prediction_model_experiments.ipynb`**: Machine Learning model experiments (`RandomForestRegressor` vs `LinearRegression`) for crowd density forecasting.

---

## 🗓️ 8-Week Milestone Execution Plan

- [x] **Milestone 1 (Week 1 & 2)**: Project Definition, Dataset Selection, Schema Design & EDA Notebooks.
- [ ] **Milestone 2 (Week 3 & 4)**: AI Model Training, Evaluation & FastAPI Backend Endpoint Implementation.
- [ ] **Milestone 3 (Week 5 & 6)**: React Dashboard UI Setup, Real-Time Station Heatmaps & Alert Center.
- [ ] **Milestone 4 (Week 7 & 8)**: System Integration, End-to-End Testing & Final Presentation.

---

## 📁 Repository Structure

```
.
├── datasets/
│   ├── metro_ridership_dataset.csv   # Historical Ticketing & Turnstile Logs
│   ├── train_schedules_dataset.csv   # Train Timetables & Delay Logs
│   └── station_master_dataset.csv    # Station Metadata & Capacity Limits
├── notebooks/
│   ├── 01_exploratory_data_analysis.ipynb          # Milestone 1 EDA Analysis
│   └── 02_crowd_prediction_model_experiments.ipynb # Milestone 2 ML Experiments
├── backend/
│   └── README.md                     # Backend Service Placeholder
├── frontend/
│   └── README.md                     # Frontend Service Placeholder
└── README.md                         # Milestone 1 Submission Documentation
```
