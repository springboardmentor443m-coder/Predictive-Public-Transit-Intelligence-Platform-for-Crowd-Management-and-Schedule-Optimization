# MetroFlow Official Data Source Registry

This document serves as the single source of truth for all transportation data sources integrated into the MetroFlow Platform.

---

## 1. Primary Historical Dataset — MTA Subway Hourly Ridership (2022–2024)

- **SOURCE**: NYC Open Data / Metropolitan Transportation Authority (MTA)
- **TYPE**: Historical Turnstile & Tap Ridership Data
- **PROVIDER**: NYC MTA / Open Data Portal
- **OFFICIAL URL**: [MTA Subway Hourly Ridership Dataset](https://data.ny.gov/Transportation/MTA-Subway-Hourly-Ridership-Beginning-2022/wujg-7c2s)
- **HISTORICAL / LIVE**: Historical
- **UPDATE FREQUENCY**: Daily batch updates from MTA
- **TIME RANGE**: January 1, 2022 – December 31, 2024 (3 full years)
- **VOLUME**: 302,173 clean hourly station records (Top 12 Hub Complex subset)
- **IMPORTANT FIELDS**:
  - `transit_timestamp`: Hourly bucket timestamp (`YYYY-MM-DD HH:00:00`)
  - `station_complex_id`: Official MTA Station Complex Unique ID
  - `station_complex`: Human-readable station complex name
  - `borough`: NYC Borough (`Manhattan`, `Queens`)
  - `passenger_count`: Observed hourly entry taps / turnstile count
  - `transfers`: Observed system-to-system transfer counts (where recorded)
  - `latitude` & `longitude`: Station complex centroid coordinates
  - `routes`: Serving subway lines / routes (e.g., `1 2 3`, `A C E`, `4 5 6 7 S`)
  - `structure`: Station structural type (`Subway`, `Elevated`, `Open Cut`)
  - `ada`: ADA Accessibility flag (`True` / `False`)
- **WHAT IT CAN SUPPORT**:
  - Hourly station entry demand monitoring & historical trend analysis
  - Chronological ML demand forecasting & congestion risk scoring
  - Peak-hour passenger flow analysis and time-series feature engineering
- **WHAT IT CANNOT SUPPORT**:
  - **Exact passenger exits**: Exits are unrecorded in MTA tap-in / turnstile systems.
  - **Onboard physical train occupancy**: Passenger counts represent station entry points, not live train interior crowding.

---

## 2. Secondary Historical Dataset — MTA Service Status & Incidents (2022–2024)

- **SOURCE**: MTA Operational Performance Reports
- **TYPE**: Monthly Line-Level Incident Summaries
- **PROVIDER**: NYC MTA Operations
- **OFFICIAL URL**: [MTA Performance Metrics](https://metrics.mta.info/)
- **HISTORICAL / LIVE**: Historical
- **UPDATE FREQUENCY**: Monthly
- **TIME RANGE**: 2022–2024 (24,955 incident records)
- **IMPORTANT FIELDS**: `month`, `division`, `line`, `day_type`, `incidents`, `reporting_category`
- **WHAT IT CAN SUPPORT**:
  - Line-level incident frequency and delay impact feature engineering
  - Historical correlation between service disruptions and station crowding
- **WHAT IT CANNOT SUPPORT**:
  - Real-time minute-by-minute incident dispatching (historical aggregation only).

---

## 3. Real-Time Feed 1 — MTA GTFS-Realtime Vehicle Positions

- **SOURCE**: NYC MTA GTFS-RT Protobuf Feeds
- **TYPE**: Real-Time Vehicle Position Stream
- **PROVIDER**: MTA Realtime API
- **OFFICIAL URL**: `https://api-endpoint.mta.info/Dataservice/mtagtfsfeeds/nyct%2Fgtfs*`
- **HISTORICAL / LIVE**: **LIVE**
- **UPDATE FREQUENCY**: Every 30 seconds
- **IMPORTANT FIELDS**:
  - `vehicle_id`: Unique transit train identifier
  - `trip_id`: GTFS Trip ID mapping to static schedule
  - `route_id`: Subway line route (e.g., `1`, `A`, `7`, `L`, `N`)
  - `current_stop_id`: GTFS stop identifier where train is currently located
  - `current_status`: `INCOMING_AT`, `STOPPED_AT`, or `IN_TRANSIT_TO`
  - `timestamp`: UTC observation timestamp
  - `latitude` & `longitude`: Geolocation coordinates
- **WHAT IT CAN SUPPORT**:
  - Live train tracking across active subway lines
  - Real-time vehicle location visualization on operations monitoring screens
- **WHAT IT CANNOT SUPPORT**:
  - **Passenger count / occupancy**: GTFS-RT VehiclePositions feeds do not include physical passenger weight/load sensors. Field is explicitly populated as `None`.

---

## 4. Real-Time Feed 2 — MTA GTFS-Realtime Trip Updates & Delays

- **SOURCE**: NYC MTA GTFS-RT Protobuf Feeds
- **TYPE**: Real-Time Estimated Arrival & Delay Stream
- **PROVIDER**: MTA Realtime API
- **OFFICIAL URL**: `https://api-endpoint.mta.info/Dataservice/mtagtfsfeeds/nyct%2Fgtfs*`
- **HISTORICAL / LIVE**: **LIVE**
- **UPDATE FREQUENCY**: Every 30 seconds
- **IMPORTANT FIELDS**:
  - `trip_id`: GTFS Trip ID
  - `route_id`: Route / Line identifier
  - `stop_id`: Target station GTFS stop ID
  - `delay_seconds`: Real-time schedule deviation in seconds
  - `estimated_arrival` & `estimated_departure`: Predicted arrival/departure timestamps
- **WHAT IT CAN SUPPORT**:
  - Real-time line delay monitoring and station ETA tracking
- **WHAT IT CANNOT SUPPORT**:
  - Automatic physical signal interlocking control (read-only advisory feed).

---

## 5. Real-Time Feed 3 — MTA GTFS-Realtime Service Alerts

- **SOURCE**: NYC MTA Service Alert Feed
- **TYPE**: Official Service Status & Delay Notices
- **PROVIDER**: MTA Realtime API
- **OFFICIAL URL**: `https://api-endpoint.mta.info/Dataservice/mtagtfsfeeds/cservice%2Falerts`
- **HISTORICAL / LIVE**: **LIVE**
- **UPDATE FREQUENCY**: Real-time push / 30s poll
- **IMPORTANT FIELDS**: `alert_id`, `header_text`, `description_text`, `affected_routes`, `affected_stops`, `active_period`
- **WHAT IT CAN SUPPORT**:
  - Live system alert broadcasting to transit operators
- **WHAT IT CANNOT SUPPORT**:
  - Automated resolution of mechanical or track disruptions.
