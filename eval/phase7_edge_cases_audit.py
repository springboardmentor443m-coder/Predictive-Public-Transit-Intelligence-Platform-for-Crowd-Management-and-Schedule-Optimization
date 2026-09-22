import os
import sys
import math
import joblib
import numpy as np
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

from fastapi.testclient import TestClient
from app.main import app
from app.ml.model_loader import ml_model
from app.ml.delay_model_loader import delay_ml_model
from app.services.scheduling import recommend_frequency

print("=" * 80)
print("METROFLOW AUDIT - PHASE 7: Edge Cases in ML Pipeline & Optimization Logic")
print("=" * 80)

# Preload models
ml_model.load_model()
delay_ml_model.load_model()
client = TestClient(app)

# 1. Edge Case 1: Station Code Not Seen During Training
print("\n[1] AUDIT: Unseen Station Codes Handling")
print("-" * 80)

unseen_codes = ["99999", "-1", "7777", "AIRPORT_EXPRESS", "UNKNOWN_STN"]
now = datetime(2026, 9, 22, 8, 30, 0, tzinfo=timezone.utc)

print("A. Testing at Model Loader Level (ml_model.predict):")
for code in unseen_codes:
    try:
        pred_density, label = ml_model.predict(station_code=code, timestamp=now)
        print(f"  Station Code '{code:<16}': Success -> Predicted Density = {pred_density:>6.1f}%, Congestion = '{label}'")
    except Exception as e:
        print(f"  Station Code '{code:<16}': CRASHED -> {type(e).__name__}: {e}")

print("\nB. Testing at API Service Level (POST /api/v1/predict/crowd):")
for code in unseen_codes:
    resp = client.post("/api/v1/predict/crowd", json={"station_code": code, "timestamp": now.isoformat()})
    print(f"  Station Code '{code:<16}': HTTP {resp.status_code} -> {resp.json().get('detail', resp.json())}")

print("\nC. Testing Delay Model on Unseen Stations & Encodings (delay_ml_model.predict):")
delay_test_cases = [
    ("99999", "Clear", "Spring"),
    ("UNKNOWN_STN", "Tornado_Unknown", "Monsoon_Unknown"),
    ("-500", "Hailstorm", "Polar_Night"),
]
for code, weather, season in delay_test_cases:
    try:
        has_delay, delay_prob = delay_ml_model.predict(
            station_code=code,
            line_num=2,
            timestamp=now,
            weather_condition=weather,
            season=season,
        )
        print(f"  Station '{code:<12}' | Weather '{weather:<16}' | Season '{season:<14}': Success -> Delay={has_delay}, Prob={delay_prob:.4f}")
    except Exception as e:
        print(f"  Delay Model CRASHED on '{code}': {type(e).__name__}: {e}")

# 2. Edge Case 2: Extreme and Conflicting Feature Values
print("\n[2] AUDIT: Extreme & Conflicting Feature Values in Crowd Model")
print("-" * 80)

# Build manual DataFrames directly against the scikit-learn model artifact
feature_cols = [
    'station_code', 'line_num', 'year', 'hour', 'day_of_week', 'is_weekend',
    'month', 'is_morning_peak', 'is_evening_peak', 'latitude', 'longitude'
]

scenarios = [
    ("Baseline (Normal morning peak 08:00)",
     {'station_code': 222, 'line_num': 2, 'year': 2026, 'hour': 8, 'day_of_week': 1, 'is_weekend': 0,
      'month': 9, 'is_morning_peak': 1, 'is_evening_peak': 0, 'latitude': 37.4979, 'longitude': 127.0276}),
    ("Baseline (Normal evening peak 18:00)",
     {'station_code': 222, 'line_num': 2, 'year': 2026, 'hour': 18, 'day_of_week': 1, 'is_weekend': 0,
      'month': 9, 'is_morning_peak': 0, 'is_evening_peak': 1, 'latitude': 37.4979, 'longitude': 127.0276}),
    ("CONFLICT: Both morning & evening peak = 1 at 08:00",
     {'station_code': 222, 'line_num': 2, 'year': 2026, 'hour': 8, 'day_of_week': 1, 'is_weekend': 0,
      'month': 9, 'is_morning_peak': 1, 'is_evening_peak': 1, 'latitude': 37.4979, 'longitude': 127.0276}),
    ("CONFLICT: Both morning & evening peak = 1 at 18:00",
     {'station_code': 222, 'line_num': 2, 'year': 2026, 'hour': 18, 'day_of_week': 1, 'is_weekend': 0,
      'month': 9, 'is_morning_peak': 1, 'is_evening_peak': 1, 'latitude': 37.4979, 'longitude': 127.0276}),
    ("CONFLICT: Both peaks = 0 at rush hour 08:00",
     {'station_code': 222, 'line_num': 2, 'year': 2026, 'hour': 8, 'day_of_week': 1, 'is_weekend': 0,
      'month': 9, 'is_morning_peak': 0, 'is_evening_peak': 0, 'latitude': 37.4979, 'longitude': 127.0276}),
    ("EXTREME: Hour = 35 (impossible hour)",
     {'station_code': 222, 'line_num': 2, 'year': 2026, 'hour': 35, 'day_of_week': 1, 'is_weekend': 0,
      'month': 9, 'is_morning_peak': 0, 'is_evening_peak': 0, 'latitude': 37.4979, 'longitude': 127.0276}),
    ("EXTREME: Hour = -5 (negative hour)",
     {'station_code': 222, 'line_num': 2, 'year': 2026, 'hour': -5, 'day_of_week': 1, 'is_weekend': 0,
      'month': 9, 'is_morning_peak': 0, 'is_evening_peak': 0, 'latitude': 37.4979, 'longitude': 127.0276}),
    ("EXTREME: Coordinates outside Earth (lat=999, lon=-999)",
     {'station_code': 222, 'line_num': 2, 'year': 2026, 'hour': 8, 'day_of_week': 1, 'is_weekend': 0,
      'month': 9, 'is_morning_peak': 1, 'is_evening_peak': 0, 'latitude': 999.0, 'longitude': -999.0}),
    ("EXTREME: Distant future year 2099",
     {'station_code': 222, 'line_num': 2, 'year': 2099, 'hour': 8, 'day_of_week': 1, 'is_weekend': 0,
      'month': 9, 'is_morning_peak': 1, 'is_evening_peak': 0, 'latitude': 37.4979, 'longitude': 127.0276}),
]

print(f"{'Scenario':<55} | {'Raw Model Output':<18} | {'Status'}")
print("-" * 88)

for name, row in scenarios:
    test_df = pd.DataFrame([row])[feature_cols]
    pred_val = float(ml_model.model.predict(test_df)[0])
    # Check if prediction is within standard historical bounds (0 to 20,000 passenger flow)
    is_sane = 0.0 <= pred_val <= 20000.0
    status_str = "Sane (Bounded)" if is_sane else "OUT OF BOUNDS"
    print(f"{name:<55} | {pred_val:>14.2f}     | {status_str}")

# 3. Edge Case 3: Headway Optimization Formula Boundaries
print("\n[3] AUDIT: Headway Optimization Formula Boundary Verification")
print("-" * 80)
print("Formula Claimed in README Line 190:")
print("  Optimal Headway (min) = max(2.0, min(8.0, K_base / max(1.0, Density / 25.0)))")

def compute_claimed_headway(density: float, k_base: float = 5.0) -> float:
    denom = max(1.0, density / 25.0)
    raw = k_base / denom
    return max(2.0, min(8.0, raw))

test_densities = [-50.0, 0.0, 10.0, 25.0, 40.0, 68.0, 86.0, 100.0, 150.0, 1000.0]

print(f"\nEvaluating Claimed Formula across Densities for K_base = 5.0 (Standard Seoul Base Headway):")
print(f"{'Density (%)':<15} | {'Raw Headway':<15} | {'Clamped Optimal Headway':<25} | {'Within [2.0, 8.0] Bound?'}")
print("-" * 80)

for d in test_densities:
    denom = max(1.0, d / 25.0)
    raw = 5.0 / denom if denom != 0 else float('inf')
    clamped = compute_claimed_headway(d, k_base=5.0)
    in_bounds = 2.0 <= clamped <= 8.0
    print(f"{d:>8.1f}%       | {raw:>10.2f} min  | {clamped:>12.2f} min            | {'YES (PASS)' if in_bounds else 'FAIL'}")

print("\nEvaluating Live Codebase Implementation (recommend_frequency in scheduling.py & SchedulePage.tsx):")
print(f"{'Density (%)':<15} | {'Congestion Label':<18} | {'Backend Action String':<40} | {'Frontend Headway'}")
print("-" * 95)

for d in [0.0, 25.0, 50.0, 75.0, 95.0]:
    label = ml_model._classify_congestion(d)
    rec = recommend_frequency(d, label)
    # Frontend mapping (SchedulePage.tsx lines 55-67)
    if label == 'critical':
        fe_headway = 3.5
    elif label == 'high':
        fe_headway = 4.0
    elif label == 'medium':
        fe_headway = 5.0
    else:
        fe_headway = 6.0
    print(f"{d:>8.1f}%       | {label:<18} | {rec['recommended_action']:<40} | {fe_headway:.1f} min")

print("\n" + "=" * 80)
print("PHASE 7 AUDIT COMPLETE")
print("=" * 80)
