# MetroFlow — System Architecture & Schema (Week 1 & 2)

## High-level architecture (current scope)

```
┌─────────────────────────────────────────────┐
│              Client (Swagger/UI)             │
└───────────────────┬───────────────────────────┘
                     │ HTTPS (JWT bearer)
┌───────────────────▼───────────────────────────┐
│                FastAPI App (app/main.py)       │
│  ┌───────────────┐   ┌───────────────────────┐│
│  │ User Mgmt     │   │ Crowd Monitoring       ││
│  │ (core/security│   │ (services/             ││
│  │  .py) - JWT,  │   │  crowd_monitoring.py)  ││
│  │  RBAC         │   │                        ││
│  └───────────────┘   └───────────┬────────────┘│
└──────────────────────────────────┼──────────────┘
                                    │
                     ┌──────────────▼──────────────┐
                     │  Data Repository             │
                     │  (app/data/repository.py)    │
                     │  pandas over CSV, cached     │
                     └──────────────┬──────────────┘
                                    │
                     ┌──────────────▼──────────────┐
                     │  taipei_mrt_2yr.csv           │
                     │  Date, Hour, Station,        │
                     │  Entries, Exits               │
                     │  (real-schema, 2yr, hourly)  │
                     └───────────────────────────────┘
```

Weeks 3+ will slot Scheduling, AI Prediction, Alerts, and Analytics services
into the same layer alongside Crowd Monitoring — the repository and auth
layer built now don't change.

## Database schema (logical)

Right now the data layer is a single flat fact table (mirroring the real
open dataset exactly, so the swap-in later is trivial). As modules are added
week by week, this grows into a small star schema:

**`ridership_fact`** (current — `taipei_mrt_2yr.csv`)
| column  | type | notes                          |
|---------|------|---------------------------------|
| Date    | date | one row per station per hour   |
| Hour    | int  | 0–23                            |
| Station | str  | station name (join key)        |
| Entries | int  | passengers entering that hour  |
| Exits   | int  | passengers exiting that hour   |

**`users`** (`core/security.py`, in-memory demo store — swap for a real
users table, e.g. Postgres, in Week 7/8 deployment hardening)
| column           | type | notes                        |
|------------------|------|-------------------------------|
| username          | str  | primary key                  |
| hashed_password   | str  | bcrypt                       |
| role              | str  | `admin` \| `operator`        |
| full_name         | str  |                                |
| assigned_station  | str  | nullable, operator scoping   |

Planned additions for later weeks (not built yet):
- `station_dim` (capacity, line, lat/long) — replaces the flat `DEFAULT_HOURLY_CAPACITY` constant once real capacity data is available
- `schedules` (Week 3&4 — Scheduling module)
- `alerts_log` (Week 5&6 — Alert & Notification module)
- `model_metadata` (Week 3&4 — AI Prediction module: stores trained model version, MAE/MAPE)

## Tech stack used so far

- **Backend**: Python, FastAPI
- **Data**: pandas, CSV (schema-compatible with the real official dataset)
- **Auth**: python-jose (JWT), passlib (bcrypt)
- Matches the tech stack in the project brief (Section 7); Redis/Postgres/Mongo,
  TensorFlow/scikit-learn, and Docker come in as later weeks need them —
  no point standing up infrastructure Week 1&2's scope doesn't use yet.
