# MetroFlow: Predictive Public Transit Intelligence Platform for Crowd Management and Schedule Optimization
### 🎓 Infosys Springboard Internship Project Submission — Milestone 2 (Week 3 & 4)

---

## 📌 Milestone 2 Overview: Scheduling System & AI Prediction Models

In **Milestone 2**, we implemented the Machine Learning crowd prediction engine, train frequency optimization algorithm, and backend API scheduling workflows.

### 🌟 What Has Been Completed for Milestone 2:

1. **AI Machine Learning Model Training (`backend/train_model.py`)**:
   - Built and trained a `RandomForestRegressor` model on `NYC_subway_traffic_2017-2021.csv`.
   - Feature engineering: Encoded station names, boroughs, hour of day, day of week, and month.
   - Model accuracy: Achieved $R^2 \approx 0.8665$ score for predicting passenger traffic surges.
   - Saved trained model artifacts: `crowd_model.pkl` and `encoders.pkl`.

2. **Pre-Rendered Model Experiments Notebook (`notebooks/02_crowd_prediction_model_experiments.ipynb`)**:
   - Compares **RandomForestRegressor** vs **LinearRegression** baseline.
   - Pre-rendered outputs with execution counts, evaluation metrics, and feature importance horizontal bar chart image.

3. **AI Prediction & Inference Engine (`backend/app/ml_engine.py`)**:
   - Loads `crowd_model.pkl` and evaluates passenger congestion risk levels (`Low`, `Moderate`, `High`, `Critical`).
   - Automatically generates train frequency recommendations (e.g. *"Dispatch +3 Extra Trains, set interval to 3.5 mins"*).

4. **FastAPI Backend REST Endpoints (`backend/app/main.py`)**:
   - `/api/predict`: Returns dynamic AI crowd forecasts and recommendations.
   - `/api/trains` & `/api/trains/{id}`: Enables train timetable management and frequency adjustments.

---

## 📁 Milestone 2 Repository Structure (`E:\MetroFlow_Submission`)

```
.
├── datasets/
│   └── NYC_subway_traffic_2017-2021.csv         # Primary Dataset (25,200 Rows | 3.95 MB)
├── notebooks/
│   ├── 01_exploratory_data_analysis.ipynb        # Milestone 1: Pre-rendered EDA Notebook
│   └── 02_crowd_prediction_model_experiments.ipynb # Milestone 2: Pre-rendered ML Experiments Notebook
├── backend/
│   ├── app/
│   │   ├── main.py          # FastAPI REST Endpoints (/api/predict, /api/trains)
│   │   └── ml_engine.py     # AI Prediction & Recommendation Engine
│   ├── train_model.py       # ML Model Training Script
│   ├── crowd_model.pkl      # Saved Trained Model Artifact
│   ├── encoders.pkl         # Saved Label Encoders Artifact
│   └── requirements.txt     # Python Dependencies
├── frontend/
│   └── README.md            # Frontend Placeholder (Scheduled for Milestone 3 & 4)
└── README.md                # Milestone 2 Submission Documentation
```
