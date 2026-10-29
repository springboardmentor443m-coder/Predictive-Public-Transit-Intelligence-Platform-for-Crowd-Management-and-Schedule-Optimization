# MetroFlow: AI-Powered Public Transit Intelligence Platform

## 1. Project Overview

MetroFlow is an AI-based public transit intelligence platform designed to support metro crowd management, ridership prediction, analytics, and train schedule optimization.

The system uses historical metro ridership data to predict passenger demand at selected stations and hours. It displays prediction results, crowd levels, alerts, ridership trends, and recommended train frequencies through a web dashboard.

## 2. Problem Statement

Metro stations can experience heavy passenger traffic during peak hours. Without reliable demand estimates, transport authorities may find it difficult to identify congestion periods and plan suitable train frequencies.

MetroFlow aims to support better planning by using historical ridership data and machine learning to estimate passenger demand and provide actionable recommendations.

## 3. Project Objectives

- Predict metro ridership for a selected station and hour.
- Classify predicted crowd levels as LOW, MEDIUM, or HIGH.
- Display passenger demand trends through analytics charts.
- Identify peak ridership hours and stations.
- Generate crowd alerts and recommended actions.
- Suggest train frequency based on predicted crowd levels.
- Provide an easy-to-use React dashboard for viewing results.

## 4. Technologies Used

| Technology | Purpose |
|---|---|
| Python | Backend logic and machine learning |
| Pandas | Data loading and preprocessing |
| Scikit-learn | Random Forest regression model |
| FastAPI | Backend API development |
| Uvicorn | Running the FastAPI server |
| React.js | Interactive dashboard |
| Vite | Frontend development server |
| HTML and CSS | Dashboard structure and styling |
| Git and GitHub | Version control and project hosting |

## 5. System Architecture

The project follows this workflow:

1. Historical ridership data is loaded and processed.
2. A Random Forest regression model learns patterns from the dataset.
3. The FastAPI backend receives station and hour inputs.
4. The model predicts ridership for the requested inputs.
5. The backend determines the crowd level and recommendation.
6. The React frontend displays predictions, alerts, analytics, and schedule suggestions.

## 6. Main Features

### 6.1 Ridership Prediction

Users select a metro station and hour to receive an estimated ridership value.

### 6.2 Crowd Classification

Predicted ridership is classified using the project's current thresholds:

- LOW: fewer than 100
- MEDIUM: 100 to fewer than 300
- HIGH: 300 or more

### 6.3 Crowd Alerts

The dashboard displays warnings when high passenger demand is predicted and presents suggested actions for managing congestion.

### 6.4 Analytics Dashboard

The analytics section presents hourly ridership trends, station-level ridership comparisons, and peak-hour information.

### 6.5 Schedule Optimization

The current recommendation rules suggest:

- HIGH crowd: train frequency every 5 minutes
- MEDIUM crowd: train frequency every 8 minutes
- LOW crowd: train frequency every 12 minutes

These are prototype recommendations, not live changes to actual metro operations.

## 7. Machine Learning Model

The project uses `RandomForestRegressor` from Scikit-learn.

The model uses features including:

- Hour
- Year
- Month
- Day of the month
- Day of the week
- Encoded station

The target variable is ridership.

### Model Evaluation

Previously recorded evaluation results:

| Metric | Result |
|---|---:|
| Mean Absolute Error (MAE) | 41.12 |
| Root Mean Squared Error (RMSE) | 87.56 |
| R² score | 0.9682 |

These results come from the earlier model evaluation. They should be confirmed against the final training and test configuration before submission.

## 8. Project Structure

The main project components include:

- `backend/model.py` — machine learning model and data preparation
- `backend/main.py` — FastAPI application and API endpoints
- `frontend/src/App.jsx` — React dashboard
- `dataset/` — historical ridership datasets
- `notebooks/` — model analysis and prediction experiments

Other configuration files support frontend setup, dependencies, and version control.

## 9. Running the Project

### Backend

Open a terminal in the project root directory and run:

```bash
python -m uvicorn backend.main:app --reload
```

Backend URL: `http://127.0.0.1:8000`

API documentation: `http://127.0.0.1:8000/docs`

### Frontend

Open a second terminal and run:

```bash
cd frontend
npm install
npm run dev
```

Open the local URL printed by Vite, usually `http://localhost:5173`.

Keep both development servers running while using the dashboard.

## 10. Testing

The following areas should be tested before final submission:

- Ridership prediction for valid stations and hours
- Handling of unknown station names and invalid hours
- Crowd-level classification
- Analytics endpoint responses and charts
- Schedule recommendation rules
- Backend/frontend connectivity
- Dashboard layout and error messages

Record the actual results of each test before marking it as passed.

## 11. Limitations

- Predictions depend on the quality and coverage of the available historical dataset.
- Forecasts are estimates and may not represent actual passenger counts.
- Real-time passenger feeds and live metro-control integration are not established features of the current prototype.
- Schedule recommendations are rule-based suggestions and do not automatically change real train schedules.
- The system does not use CCTV image processing or computer vision.

## 12. Future Scope

- Integrate validated live ridership or sensor data.
- Compare additional forecasting algorithms.
- Improve model evaluation and forecasting accuracy.
- Add configurable alert thresholds and notification channels.
- Develop more advanced schedule optimization.
- Add user authentication and deployment.
- Monitor model performance as new data becomes available.

## 13. Conclusion

MetroFlow demonstrates how machine learning, APIs, and a web dashboard can support metro ridership forecasting and crowd-management planning. It combines prediction, analytics, alerts, and rule-based schedule recommendations in a single prototype.

The project can be extended with more comprehensive datasets, further testing, and validated real-time integrations.

