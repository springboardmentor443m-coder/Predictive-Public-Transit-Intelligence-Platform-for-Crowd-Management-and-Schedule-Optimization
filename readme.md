MetroFlow — AI-Powered Metro Crowd Management and Scheduling Platform

MetroFlow is an AI-powered platform designed to support metro crowd monitoring, demand forecasting, delay prediction, scheduling, alerts, and operational analytics.

Project Status

Milestone 3 (Week 6) completed.

Milestones 1, 2, and 3 are complete. The remaining work is planned for Milestone 4, covering testing and validation, UI responsiveness, Docker/cloud deployment, and final project documentation and presentation.

Development Scope

Weeks 1–2 — User Management and Crowd Monitoring

The first phase established secure user access and real-time crowd monitoring capabilities.

Key features include:

JWT-based authentication

Role-based access for administrators and operators

Live station congestion monitoring

Station-level analytics

Congestion heatmap visualization

Weeks 3–4 — Scheduling and AI Prediction

The second phase introduced data-driven scheduling and AI-based forecasting.

Key features include:

Real per-station hourly capacity instead of a fixed 6,000-passenger placeholder

Simulated train-delay data correlated with congestion patterns

AI demand forecasting using a Random Forest model

Prediction of passenger entries by station and hour

AI-based delay forecasting by station and hour

Train-frequency recommendations

Peak-hour summaries

Delay-aware schedule adjustments

Week 5 — Alerts and Notifications

The alerting system provides both real-time and predictive notifications.

Key features include:

Live overcrowding alerts based on station-specific capacity

Forecasted overcrowding alerts generated before congestion occurs

Delay notifications based on the delay dataset

Emergency announcements restricted to administrators

A consolidated real-time alert feed for dashboard monitoring

Week 6 — Analytics Dashboard

Milestone 3 was completed with the introduction of the analytics dashboard.

The dashboard provides:

System-wide passenger traffic analysis

Identification of the busiest and quietest stations

Station performance analysis combining crowd, delay, and AI insights

Live operational monitoring, including system health and active delays

Congestion heatmap analysis with worst-congestion-point rankings

Standalone AI insights, including forecast curves and recommendations

Upcoming Development

The following components remain under Milestone 4 (Weeks 7–8):

Application testing and validation

UI responsiveness improvements

Docker-based deployment

Cloud deployment

Final documentation

Final project presentation

Datasets

MetroFlow currently uses three datasets located in the app/data/ directory.

Taipei MRT Ridership Dataset

File: app/data/taipei_mrt_2yr.csv

Schema: Date, Hour, Station, Entries, Exits

This dataset contains two years of hourly ridership information covering 30 real Taipei MRT stations.

Station Capacity Dataset

File: app/data/station_capacity.csv

Schema: Station, HourlyCapacity

This dataset defines hourly capacity for individual stations. Capacity varies according to station tier, such as interchange stations and outer stations.

Train Delay Dataset

File: app/data/train_delays.csv

Schema: Date, Hour, Station, DelayMinutes

This dataset contains simulated train-delay events designed to reflect congestion-related patterns, with busier periods associated with more frequent or longer delays.

All three datasets follow real-world open-data schemas. As a result, they can be replaced with genuine official datasets in the future without requiring changes to the application's core code.

Installation and Setup

Install the required Python dependencies:

python -m pip install -r requirements.txt

Start the FastAPI application:

python -m uvicorn app.main:app --reload --port 8000

Once the application is running, open the FastAPI documentation at:

http://127.0.0.1:8000/docs

Demo Credentials

Administrator

Username: admin

Password: admin123

Access: Full system access

Operator

Username: operator1

Password: operator123

Access: Station-scoped access

Note: These credentials are intended for demonstration purposes only and should be replaced or secured before production deployment.

AI Model Initialization

For first-time setup, an administrator can train the demand and delay prediction models by calling:

POST /ai/train

Once trained, the models provide predictions without requiring retraining for every request.

If the training endpoint is skipped, the prediction endpoints automatically train the models when they are first used.

API Endpoints

User Management

POST /auth/login — Authenticate a user

GET /auth/me — Retrieve the current user's information

GET /admin/ping — Verify administrator access

Crowd Monitoring

GET /stations — Retrieve available stations

GET /stations/capacity — Retrieve station capacity information

GET /crowd/live — Retrieve live crowd information

GET /crowd/station/{station} — Retrieve crowd information for a station

GET /crowd/analytics/{station} — Retrieve station-level crowd analytics

GET /crowd/heatmap — Retrieve congestion heatmap data

AI Prediction

POST /ai/train — Train the AI models

GET /ai/predict/demand/{station} — Predict station demand

GET /ai/predict/delay/{station} — Predict expected delay

GET /ai/forecast/{station} — Generate a 24-hour forecast

GET /ai/recommendations/{station} — Generate AI-based recommendations

Scheduling

GET /schedule/{station} — Retrieve station scheduling information

GET /schedule/{station}/peak-summary — Retrieve peak-hour summary

GET /schedule/{station}/delay-report — Retrieve delay report

GET /schedule/{station}/adjust-for-delay — Generate delay-aware schedule adjustments

Alerts and Notifications

GET /alerts/overcrowding — Retrieve current overcrowding alerts

GET /alerts/forecasted/{station} — Retrieve predicted overcrowding alerts

GET /alerts/delays — Retrieve delay notifications

POST /alerts/emergency — Create an emergency announcement

GET /alerts/live-feed — Retrieve the live alert feed

Analytics Dashboard

GET /analytics/traffic — Generate system-wide traffic analysis

GET /analytics/station/{station} — Generate station performance analysis

GET /analytics/operational-summary — Retrieve the operational monitoring summary

GET /analytics/heatmap-report — Generate a congestion heatmap report

GET /analytics/ai-insights/{station} — Retrieve AI-generated station insights

System

GET / — Application root endpoint

GET /health — Health-check endpoint
