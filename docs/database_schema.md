# MetroFlow Database Schema

## 1. Overview

The MetroFlow database is designed to store information related to users, stations, passenger crowd data, and congestion status.

The database supports authentication, crowd monitoring, station analysis, and congestion tracking.

---

## 2. Users Table

Stores information about system users.

| Field | Description |
|---|---|
| user_id | MongoDB document identifier |
| email | Unique user email |
| password_hash | Salted PBKDF2 password hash |
| role | Admin or Operator |

The backend stores users in the MongoDB `metroflow.users` collection and
creates a unique index on `email` during startup. Configure the connection
with `MONGODB_URI` and `MONGODB_DATABASE`. The initial demo users are seeded
from `METROFLOW_ADMIN_PASSWORD` and `METROFLOW_OPERATOR_PASSWORD`; the
development defaults are `admin123` and `operator123`.

After a successful login, the backend returns an 8-hour JWT access token.
Protected API requests must send it as `Authorization: Bearer <token>`. Set
`METROFLOW_JWT_SECRET` to a long random value outside local development.

## 3. Operations Telemetry

Live operational snapshots are stored in the MongoDB
`metroflow.operations_snapshots` collection. External transit systems can send
updates to `POST /api/v1/operations/telemetry`. The dashboard polls
`GET /api/v1/operations/summary` every 30 seconds and displays the latest
stored snapshot.

For local development, start the backend and run:

```powershell
python backend/simulate_telemetry.py --once
python backend/simulate_telemetry.py --interval 30
```

The simulator is a temporary stand-in for a real train tracking or transit
agency feed.

---

## 3. Stations Table

Stores information about public transit stations.

| Field | Description |
|---|---|
| station_id | Unique station ID |
| station_name | Name of the station |
| location | Station location |
| capacity | Maximum passenger capacity |

---

## 4. Passenger Data Table

Stores passenger and crowd information.

| Field | Description |
|---|---|
| record_id | Unique record ID |
| station_id | Station ID |
| passenger_count | Number of passengers |
| timestamp | Date and time of record |

---

## 5. Congestion Data Table

Stores congestion analysis results.

| Field | Description |
|---|---|
| congestion_id | Unique congestion record ID |
| station_id | Station ID |
| crowd_level | Low, Medium, or High |
| congestion_status | Normal or Congested |
| timestamp | Date and time |

---

## 6. Relationships

Users access the MetroFlow system based on their role.

Stations contain multiple passenger data records.

Passenger data is analyzed to generate congestion information.

Relationship flow:

Users
↓
MetroFlow System
↓
Stations
↓
Passenger Data
↓
Congestion Analysis

---

## 7. Database Workflow

1. Users log into the system.
2. Station information is stored in the database.
3. Passenger data is collected for each station.
4. The backend analyzes passenger counts.
5. Crowd levels are classified as Low, Medium, or High.
6. Congestion status is displayed on the dashboard.