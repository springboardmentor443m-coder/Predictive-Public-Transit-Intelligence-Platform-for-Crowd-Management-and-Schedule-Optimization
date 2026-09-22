import os
import sys
import time
import sqlite3
import pandas as pd
from datetime import datetime, timezone

# Add backend directory
repo_root = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
backend_dir = os.path.join(repo_root, "backend")
db_file = os.path.join(backend_dir, "metroflow.db").replace('\\', '/')
model_file = os.path.abspath(os.path.join(repo_root, "..", "crowd_prediction_rf_compressed.pkl")).replace('\\', '/')

os.environ["DATABASE_URL"] = f"sqlite:///{db_file}"
os.environ["MODEL_PATH"] = model_file

if backend_dir not in sys.path:
    sys.path.insert(0, backend_dir)

from app.database import SessionLocal
from app.models.station import Station
from app.models.ridership import RidershipLog
from app.models.train_status import TrainStatus
from app.models.alert import Alert
from app.ml.model_loader import ml_model
from app.services.alert_engine import check_and_create_alerts
from app.services.cache import cache_service
from sqlalchemy import select, func

print("=" * 80)
print("METROFLOW AUDIT - PHASE 5: Station and Data Scale Verification")
print("=" * 80)

# 1. Database Entity Row Counts
print("\n[1] AUDIT: Operational Database Inventory (metroflow.db)")
print("-" * 80)

db = SessionLocal()

# Stations
station_count = db.execute(select(func.count(Station.station_code))).scalar()
distinct_codes = db.execute(select(func.count(func.distinct(Station.station_code)))).scalar()

# Stations per Line
line_breakdown = db.execute(
    select(Station.line, func.count(Station.station_code))
    .group_by(Station.line)
    .order_by(Station.line)
).all()

print(f"Total Stations Seeded:          {station_count}")
print(f"Distinct Station Codes:         {distinct_codes}")
print("Line-by-Line Breakdown:")
for line, cnt in line_breakdown:
    print(f"  - {line:<10}: {cnt} stations")

# Ridership Logs
ridership_count = db.execute(select(func.count(RidershipLog.id))).scalar()
distinct_log_stations = db.execute(select(func.count(func.distinct(RidershipLog.station_code)))).scalar()
min_ts, max_ts = db.execute(select(func.min(RidershipLog.timestamp), func.max(RidershipLog.timestamp))).first()
distinct_timestamps = db.execute(select(func.count(func.distinct(RidershipLog.timestamp)))).scalar()

print(f"\nRidership Logs Seeded:          {ridership_count:,} rows")
print(f"Distinct Stations in Logs:      {distinct_log_stations}")
print(f"Distinct Timestamps (hours):    {distinct_timestamps} hours (14 days x 24 hrs = 336 hrs)")
print(f"Expected Formula Row Count:     {distinct_log_stations} stations x 336 hours = {distinct_log_stations * 336:,} rows")
print(f"Timestamp Time Horizon:         {min_ts} to {max_ts}")

# Train Status
train_status_count = db.execute(select(func.count(TrainStatus.id))).scalar()
print(f"\nTrain Telemetry Rows:           {train_status_count:,} records")

# Alerts
alert_count = db.execute(select(func.count(Alert.id))).scalar()
print(f"Seeded System Alerts:           {alert_count:,} records")

# 2. Reconciling Conflicting Station Claims (500+, 275+, 131+)
print("\n[2] AUDIT: Reconciling Conflicting Station Scale Claims")
print("-" * 80)
print("The codebase exhibits three distinct station numbers across different files:")
print(f"  1. '131+ Seoul Stations':")
print(f"     -> THE ONE TRUE NUMBER FOR THE APPLICATION.")
print(f"     -> Exactly 131 station objects are defined in backend/app/db/seed.py")
print(f"        and seeded into the database 'stations' table ({station_count} rows).")
print(f"     -> Displayed in frontend/src/pages/LiveMapPage.tsx line 145 (defaulting to 131).")
print()
print(f"  2. '275+ Stations':")
print(f"     -> HISTORICAL ARTIFACT ONLY. Refers to the offline historical 2015-2017 Seoul Subway dataset")
print(f"        used to train the 968MB pickled crowd model. In test_model_features.py (line 103),")
print(f"        the author simulated 275 requests by looping 5 hardcoded stations 55 times (5 * 55 = 275).")
print()
print(f"  3. '500+ Stations Handled Concurrently':")
print(f"     -> UNVERIFIED / OVERSTATED MARKETING CLAIM.")
print(f"     -> No table, dataset, seed script, or configuration with 500 stations exists in the codebase.")

# 3. Investigating "500+ Stations Handled Concurrently"
print("\n[3] AUDIT: Testing Network Scanner Load (check_and_create_alerts)")
print("-" * 80)

# Preload ML model
ml_model.load_model()

# Measure alert engine scanner runtime across all 131 active stations
# (A) Without cache (cold scan)
cache_service.client = None
t_start_cold = time.perf_counter()
alerts_cold = check_and_create_alerts(db=db, dedup_window_minutes=15)
t_cold_duration = time.perf_counter() - t_start_cold

# (B) With cache (warm scan)
class SimpleMockRedis:
    def __init__(self): self.s = {}
    def get(self, k): return self.s.get(k)
    def setex(self, k, ttl, v): self.s[k] = v
    def ping(self): return True

cache_service.client = SimpleMockRedis()
# Warm the cache
t_warm_start = time.perf_counter()
alerts_warm = check_and_create_alerts(db=db, dedup_window_minutes=15)
t_warm_duration = time.perf_counter() - t_warm_start

# (C) Repeated warm scan (100% cache hits)
t_cached_start = time.perf_counter()
alerts_cached = check_and_create_alerts(db=db, dedup_window_minutes=15)
t_cached_duration = time.perf_counter() - t_cached_start

print(f"Full-Network Alert Engine Scan across all {station_count} database stations:")
print(f"  - Cold Scan (Every station runs full ML inference):  {t_cold_duration:.2f} seconds ({t_cold_duration/station_count*1000:.1f} ms/station)")
print(f"  - Warm Scan (First caching pass):                    {t_warm_duration:.2f} seconds")
print(f"  - Cached Scan (100% Redis cache hits):               {t_cached_duration:.4f} seconds ({t_cached_duration/station_count*1000:.2f} ms/station)")

# Calculate projected 500-station runtime:
proj_cold_500 = (t_cold_duration / station_count) * 500
proj_cached_500 = (t_cached_duration / station_count) * 500
print(f"\nProjected Runtime for a theoretical 500-station scan:")
print(f"  - Cold Scan (No Cache):  {proj_cold_500:.2f} seconds")
print(f"  - Cached Scan:           {proj_cached_500:.2f} seconds")

db.close()
print("\n" + "=" * 80)
