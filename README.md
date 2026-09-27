# MetroFlow 🚇

### AI-Powered Metro Crowd Management and Schedule Optimization Platform

MetroFlow is an AI-powered decision-support platform designed to analyze metro ridership patterns, predict station crowd levels, monitor congestion, and provide operational recommendations for metro crowd management and scheduling.

The platform uses historical station-wise ridership data along with weather information to generate data-driven insights for metro operators.

---

## 🎯 Project Objective

The main objective of MetroFlow is to provide an intelligent platform for:

- Monitoring station-wise passenger demand
- Identifying crowded and congested metro stations
- Predicting next-hour passenger demand
- Classifying crowd levels
- Providing operational recommendations
- Analyzing metro ridership patterns
- Understanding the influence of weather conditions on metro demand
- Supporting data-driven metro scheduling decisions

---

## 🚀 Key Features

### 1. Metro Analytics Dashboard

The dashboard provides important metro-level KPIs including:

- Total Ridership
- Total Number of Stations
- Busiest Station
- Peak Ridership Hour

These values are calculated from the station-wise ridership dataset.

---

### 2. AI-Based Crowd Prediction

MetroFlow uses an XGBoost regression model to predict next-hour station ridership.

The prediction system considers:

- Station
- Hour of day
- Day of week
- Current ridership
- Weekend information
- Peak-hour information

The system returns:

- Predicted next-hour ridership
- Crowd level
- Operational recommendation

---

### 3. Station Crowd Monitoring

The platform provides station-wise congestion monitoring.

Stations are classified into:

- 🟢 Low
- 🟡 Medium
- 🟠 High
- 🔴 Critical

The monitoring dashboard allows users to:

- Search stations
- Filter stations by congestion level
- View station ridership
- Identify highly congested stations
- Select a station for further prediction

---

### 4. Weather and Environmental Insights

MetroFlow integrates Bengaluru weather data with metro analytics.

The dashboard provides:

- Average Temperature
- Average Humidity
- Total Rainfall
- Average Wind Speed

This information can be used alongside ridership patterns for transportation analysis.

---

### 5. Station Management

The backend provides station management APIs for:

- Creating stations
- Listing stations
- Viewing individual station details

Station information includes:

- Station name
- Location
- Latitude
- Longitude
- Capacity

---

## 🤖 Machine Learning

MetroFlow uses an XGBoost regression model for passenger demand prediction.

### Prediction Pipeline

```text
Historical Ridership Data
          ↓
Data Preprocessing
          ↓
Feature Engineering
          ↓
XGBoost Regression Model
          ↓
Next-Hour Ridership Prediction
          ↓
Crowd Level Classification
          ↓
Operational Recommendation
