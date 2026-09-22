import os
import sys
import time
import json
import random
from datetime import datetime, timezone
import numpy as np
import pandas as pd

# Configure environment BEFORE importing any backend modules
repo_root = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
backend_dir = os.path.join(repo_root, "backend")
db_file = os.path.join(backend_dir, "metroflow.db").replace('\\', '/')
model_file = os.path.abspath(os.path.join(repo_root, "..", "crowd_prediction_rf_compressed.pkl")).replace('\\', '/')

os.environ["DATABASE_URL"] = f"sqlite:///{db_file}"
os.environ["MODEL_PATH"] = model_file

if backend_dir not in sys.path:
    sys.path.insert(0, backend_dir)

from fastapi.testclient import TestClient
from app.main import app
from app.services.cache import cache_service
from app.ml.model_loader import ml_model
from app.database import engine, SessionLocal
from app.models.station import Station
from sqlalchemy import select
from concurrent.futures import ThreadPoolExecutor

print("=" * 80)
print("METROFLOW AUDIT - PHASE 4: API Performance & Load Testing Benchmark")
print("=" * 80)
print(f"Database: {os.environ['DATABASE_URL']}")
print(f"Model:    {os.environ['MODEL_PATH']}")

# Pre-load model to ensure consistent test conditions
print("\n[1] Initializing API and Pre-loading Models...")
ml_model.load_model()
print(f"ML Model Loaded: {ml_model.is_loaded}")

# Get all valid station codes from database
db = SessionLocal()
stations = db.execute(select(Station)).scalars().all()
station_codes = [s.station_code for s in stations]
db.close()
print(f"Available database stations for load test: {len(station_codes)}")

# Define realistic query distribution (top hubs queried more frequently)
major_hubs = ["150", "222", "239", "216", "318", "1004", "514", "208", "212", "916"]
major_hubs = [c for c in major_hubs if c in station_codes]
other_stations = [c for c in station_codes if c not in major_hubs]

def get_random_station():
    # 60% probability of querying top hubs, 40% other stations
    if random.random() < 0.60 and major_hubs:
        return random.choice(major_hubs)
    return random.choice(station_codes)

# In-Memory Redis Mock implementation for accurate WITH CACHE testing
class InMemoryRedisMock:
    def __init__(self):
        self.store = {}
        self.hits = 0
        self.misses = 0

    def get(self, key):
        entry = self.store.get(key)
        if entry is None:
            self.misses += 1
            return None
        val, expiry = entry
        if time.time() > expiry:
            del self.store[key]
            self.misses += 1
            return None
        self.hits += 1
        return val

    def setex(self, key, ttl_seconds, value):
        self.store[key] = (value, time.time() + ttl_seconds)

    def ping(self):
        return True

    def flushall(self):
        self.store.clear()
        self.hits = 0
        self.misses = 0

client = TestClient(app)

def run_single_predict_request(station_code, timestamp_iso):
    t_start = time.perf_counter()
    resp = client.post(
        "/api/v1/predict/crowd",
        json={"station_code": station_code, "timestamp": timestamp_iso}
    )
    t_end = time.perf_counter()
    latency_ms = (t_end - t_start) * 1000
    is_success = resp.status_code == 200
    cached = resp.json().get("cached", False) if is_success else False
    return latency_ms, is_success, cached

def run_single_stations_request():
    t_start = time.perf_counter()
    resp = client.get("/api/v1/stations")
    t_end = time.perf_counter()
    latency_ms = (t_end - t_start) * 1000
    return latency_ms, resp.status_code == 200

def benchmark_endpoint(endpoint_type, concurrency_level, num_requests, with_cache=False, redis_mock=None):
    if with_cache and redis_mock:
        cache_service.client = redis_mock
        cache_service._connected = True
    else:
        cache_service.client = None
        cache_service._connected = True

    # Generate request params
    timestamps = [
        datetime(2026, 9, 22, 8, 15 * (i % 4), 0, tzinfo=timezone.utc).isoformat()
        for i in range(num_requests)
    ]
    st_codes = [get_random_station() for _ in range(num_requests)]

    latencies = []
    successes = 0
    cached_responses = 0

    with ThreadPoolExecutor(max_workers=concurrency_level) as executor:
        if endpoint_type == "predict":
            futures = [
                executor.submit(run_single_predict_request, st_codes[i], timestamps[i])
                for i in range(num_requests)
            ]
            for f in futures:
                lat, ok, was_cached = f.result()
                latencies.append(lat)
                if ok:
                    successes += 1
                if was_cached:
                    cached_responses += 1
        elif endpoint_type == "stations":
            futures = [executor.submit(run_single_stations_request) for _ in range(num_requests)]
            for f in futures:
                lat, ok = f.result()
                latencies.append(lat)
                if ok:
                    successes += 1

    latencies = np.array(latencies)
    p50 = np.percentile(latencies, 50)
    p95 = np.percentile(latencies, 95)
    p99 = np.percentile(latencies, 99)
    mean_lat = latencies.mean()

    return {
        "concurrency": concurrency_level,
        "num_requests": num_requests,
        "mean_ms": mean_lat,
        "p50_ms": p50,
        "p95_ms": p95,
        "p99_ms": p99,
        "success_rate": (successes / num_requests) * 100,
        "cache_hit_pct": (cached_responses / num_requests) * 100 if num_requests > 0 else 0,
    }

# 2. Warm up client
print("\n[2] Warming up API client...")
for _ in range(5):
    client.get("/health")
    client.post("/api/v1/predict/crowd", json={"station_code": "222", "timestamp": "2026-09-22T08:30:00Z"})

# 3. Load Testing /predict WITHOUT Cache
print("\n[3] Load Testing POST /api/v1/predict/crowd — WITHOUT Cache (Every request runs full ML model)")
print("-" * 85)
concurrency_tiers = [1, 5, 20, 50]
requests_per_tier = {1: 30, 5: 50, 20: 50, 50: 50}

predict_no_cache_results = []
print(f"{'Concurrency':<12} | {'Requests':<10} | {'P50 (ms)':<12} | {'P95 (ms)':<12} | {'P99 (ms)':<12} | {'Mean (ms)':<12} | {'Success %'}")
print("-" * 85)

for c in concurrency_tiers:
    n_req = requests_per_tier[c]
    res = benchmark_endpoint("predict", concurrency_level=c, num_requests=n_req, with_cache=False)
    predict_no_cache_results.append(res)
    print(f"{res['concurrency']:<12} | {res['num_requests']:<10} | {res['p50_ms']:<12.2f} | {res['p95_ms']:<12.2f} | {res['p99_ms']:<12.2f} | {res['mean_ms']:<12.2f} | {res['success_rate']:<8.1f}%")

# 4. Load Testing /predict WITH Cache
print("\n[4] Load Testing POST /api/v1/predict/crowd — WITH Redis Cache (Measuring fresh hit ratio & latency)")
print("-" * 95)
redis_mock = InMemoryRedisMock()
predict_with_cache_results = []
print(f"{'Concurrency':<12} | {'Requests':<10} | {'P50 (ms)':<12} | {'P95 (ms)':<12} | {'P99 (ms)':<12} | {'Mean (ms)':<12} | {'Hit Ratio %':<12} | {'Success %'}")
print("-" * 95)

for c in concurrency_tiers:
    n_req = requests_per_tier[c]
    res = benchmark_endpoint("predict", concurrency_level=c, num_requests=n_req, with_cache=True, redis_mock=redis_mock)
    predict_with_cache_results.append(res)
    print(f"{res['concurrency']:<12} | {res['num_requests']:<10} | {res['p50_ms']:<12.2f} | {res['p95_ms']:<12.2f} | {res['p99_ms']:<12.2f} | {res['mean_ms']:<12.2f} | {res['cache_hit_pct']:<12.1f}% | {res['success_rate']:<8.1f}%")

# Fresh cache statistics from the mock
total_gets = redis_mock.hits + redis_mock.misses
total_hit_rate = (redis_mock.hits / total_gets) * 100 if total_gets > 0 else 0
print(f"\nFresh Overall Redis Cache Metrics across all simulated traffic:")
print(f"  Total Cache Queries: {total_gets}")
print(f"  Total Cache Hits:    {redis_mock.hits}")
print(f"  Total Cache Misses:  {redis_mock.misses}")
print(f"  Measured Cache Hit Ratio: {total_hit_rate:.2f}% (vs README claimed 88.4%)")

# 5. Load Testing /stations Endpoint (DB queries)
print("\n[5] Load Testing GET /api/v1/stations (Database Read of all 131 Seoul Stations)")
print("-" * 85)
stations_results = []
print(f"{'Concurrency':<12} | {'Requests':<10} | {'P50 (ms)':<12} | {'P95 (ms)':<12} | {'P99 (ms)':<12} | {'Mean (ms)':<12} | {'Success %'}")
print("-" * 85)

for c in concurrency_tiers:
    n_req = requests_per_tier[c]
    res = benchmark_endpoint("stations", concurrency_level=c, num_requests=n_req, with_cache=False)
    stations_results.append(res)
    print(f"{res['concurrency']:<12} | {res['num_requests']:<10} | {res['p50_ms']:<12.2f} | {res['p95_ms']:<12.2f} | {res['p99_ms']:<12.2f} | {res['mean_ms']:<12.2f} | {res['success_rate']:<8.1f}%")

print("\n" + "=" * 80)
print("PHASE 4 LOAD TEST COMPLETE")
print("=" * 80)
