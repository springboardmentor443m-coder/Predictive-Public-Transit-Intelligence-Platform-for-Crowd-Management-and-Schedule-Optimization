# MetroFlow — Backend & Database Layer (Phase 1)

This repository layer manages the PostgreSQL database, SQLAlchemy ORM models, Alembic migrations, and synthetic time-series data generation for the Seoul Metro crowd management platform.

---

## 1. Quickstart: Running PostgreSQL Locally

You can spin up a standalone PostgreSQL 16 instance via Docker:

```bash
docker run --name metroflow-postgres \
  -e POSTGRES_USER=postgres \
  -e POSTGRES_PASSWORD=postgres \
  -e POSTGRES_DB=metroflow_db \
  -p 5432:5432 \
  -d postgres:16-alpine
```

Or connect to an existing local PostgreSQL instance matching your `.env` connection string:
```env
DATABASE_URL=postgresql://postgres:postgres@localhost:5432/metroflow_db
```

---

## 2. Running Alembic Migrations

To apply the database schema (creating `stations`, `ridership_logs`, `train_status`, and `alerts`):

```bash
cd backend
alembic upgrade head
```

To roll back the migration if needed:
```bash
alembic downgrade -1
```

---

## 3. Running the Seed Script

The seed script loads `stations_clean.csv` (or uses the built-in Seoul Metro network across Lines 1–9), computes mathematically sound double-Gaussian rush hour distributions, generates train occupancy telemetry, and populates active/resolved alerts:

```bash
cd backend
python -m app.db.seed
```

### Seeding Logic & Mathematical Curves:
- **Weekday Ridership ($D(h)$)**: Bimodal Gaussian mixture modeling AM peak ($h \approx 8.2$, $\sigma = 1.2$) and PM peak ($h \approx 18.5$, $\sigma = 1.3$) plus midday plateau ($h \approx 12.5$) and nighttime dropoff.
- **Weekend Ridership ($W(h)$)**: Unimodal afternoon leisure & shopping curve centered at $h \approx 15.2$ ($\sigma = 3.6$).
- **Train Telemetry**: Occupancy correlated directly with hourly ridership weight ($25\% + 70\% \times \text{weight} \pm \text{noise}$) with a 5% stochastic delay probability per record.

---

## 4. Verifying Data Integrity (Sample SQL Queries)

Connect to your database via `psql` or your preferred SQL client:

```bash
psql -U postgres -d metroflow_db
```

### Query 1: Verify Station Distribution across Lines
```sql
SELECT line, COUNT(*) AS station_count
FROM stations
GROUP BY line
ORDER BY line;
```

### Query 2: Inspect Weekday AM/PM Rush-Hour Curves (e.g., Gangnam Station '222')
```sql
SELECT 
    hour, 
    AVG(inflow) AS avg_inflow, 
    AVG(outflow) AS avg_outflow
FROM ridership_logs
WHERE station_code = '222' AND is_weekend = FALSE
GROUP BY hour
ORDER BY hour ASC;
```

### Query 3: Check Current Active Alerts
```sql
SELECT 
    a.id, 
    s.name_en AS station, 
    s.line, 
    a.alert_type, 
    a.severity, 
    a.message, 
    a.created_at
FROM alerts a
LEFT JOIN stations s ON a.station_code = s.station_code
WHERE a.resolved = FALSE
ORDER BY a.created_at DESC;
```

### Query 4: Check Train Telemetry & Delays
```sql
SELECT 
    line, 
    AVG(occupancy_pct) AS avg_occupancy, 
    MAX(delay_minutes) AS max_delay, 
    COUNT(*) AS records
FROM train_status
GROUP BY line
ORDER BY line;
```
