# MetroFlow

AI Platform for Metro Crowd Management and Scheduling

## Project Overview

MetroFlow is an AI-powered platform designed to monitor passenger flow, predict crowd demand, and support metro scheduling decisions using real-world transit data.

The project focuses on combining passenger movement data with train scheduling information to build a data-driven crowd management and prediction system.

## Core Datasets

1. Passenger entry/inflow — MTA Subway Hourly Ridership
2. Passenger outflow — MTA Subway Origin-Destination Ridership Estimate
3. Train arrival/departure — MTA Subway Schedules
4. Station structure — MTA Subway Entrances & Exits

Additional delay/service and capacity data will be integrated later.

## Data Pipeline

The current data pipeline is:

MTA Open Data
→ Data Download
→ Data Cleaning
→ Hourly Aggregation
→ Station Mapping
→ Dataset Integration
→ Data Validation

## Current Progress

### Dataset Integration — Completed

Real MTA datasets have been successfully integrated for **May 5, 2025**.

Current integrated dataset:

- 9,908 station-hour records
- 417 stations
- 24 hourly timestamps
- Passenger entry/inflow
- Estimated passenger exit/outflow
- Scheduled trains
- Station and geographic information
- Time-based features
- Data availability indicators

### Data Quality

The integrated dataset has been validated for:

- Duplicate station-hour records
- Missing values
- Negative passenger counts
- Negative train counts
- Station ID compatibility
- Timestamp coverage
- Dataset consistency

Core data-quality checks passed successfully.

## Important Dataset Note

The current May 5, 2025 dataset is being used as a **validated integration dataset**.

It is not yet sufficient for training the final prediction model because reliable crowd prediction requires multiple dates and temporal patterns such as:

- Weekday vs weekend
- Different days of the week
- Different weeks/months
- Holiday effects

The next stage is to extend the same pipeline to multiple dates before developing and evaluating the ML prediction model.

## Project Structure

```text
MetroFlow/
├── data/
│   ├── raw/
│   ├── processed/
│   └── external/
├── models/
├── notebooks/
├── reports/
├── src/
│   ├── api/
│   ├── data/
│   ├── features/
│   └── ml/
├── .gitignore
└── README.md