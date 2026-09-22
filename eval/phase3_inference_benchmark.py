import os
import sys
import time
import platform
import psutil
import joblib
import numpy as np
import pandas as pd

print("=" * 80)
print("METROFLOW AUDIT - PHASE 3: Inference Speed & Throughput Benchmark")
print("=" * 80)

# 1. System & Hardware Specifications
print("\n[1] Hardware & System Environment")
print("-" * 80)
cpu_count_logical = psutil.cpu_count(logical=True)
cpu_count_physical = psutil.cpu_count(logical=False)
ram_gb = psutil.virtual_memory().total / (1024 ** 3)
cpu_freq = psutil.cpu_freq()
freq_mhz = cpu_freq.current if cpu_freq else "Unknown"

print(f"  OS:                 {platform.system()} {platform.release()} (Build {platform.version()})")
print(f"  Machine / Arch:     {platform.machine()} ({platform.processor()})")
print(f"  Python Version:     {platform.python_version()}")
print(f"  Physical CPU Cores: {cpu_count_physical}")
print(f"  Logical CPU Cores:  {cpu_count_logical}")
print(f"  CPU Frequency:      {freq_mhz} MHz")
print(f"  System Total RAM:   {ram_gb:.2f} GB")

# 2. Load Model Artifacts
print("\n[2] Loading Models for Benchmark")
print("-" * 80)

crowd_model_path = os.path.abspath("../crowd_prediction_rf_compressed.pkl")
if not os.path.exists(crowd_model_path):
    crowd_model_path = os.path.abspath("crowd_prediction_rf_compressed.pkl")

t0 = time.perf_counter()
print(f"Loading crowd regressor ({crowd_model_path})...")
crowd_model = joblib.load(crowd_model_path)
t_load_crowd = time.perf_counter() - t0
print(f"  Crowd model loaded in {t_load_crowd:.2f}s ({os.path.getsize(crowd_model_path)/(1024*1024):.1f} MB)")

t0 = time.perf_counter()
print("Loading delay classifier (delay_prediction_rf_v2.pkl)...")
delay_model = joblib.load("delay_prediction_rf_v2.pkl")
t_load_delay = time.perf_counter() - t0
print(f"  Delay model loaded in {t_load_delay:.2f}s ({os.path.getsize('delay_prediction_rf_v2.pkl')/(1024*1024):.1f} MB)")

# Helper to create single-prediction features
def make_single_crowd_df():
    return pd.DataFrame([{
        'station_code': 222,
        'line_num': 2,
        'year': 2026,
        'hour': 8,
        'day_of_week': 1,
        'is_weekend': 0,
        'month': 9,
        'is_morning_peak': 1,
        'is_evening_peak': 0,
        'latitude': 37.4979,
        'longitude': 127.0276
    }])

def make_single_delay_df():
    return pd.DataFrame([{
        'station_code': 222,
        'line_num': 2,
        'hour': 8,
        'day_of_week': 1,
        'is_weekend': 0,
        'is_holiday': 0,
        'season': 0,
        'weather_condition': 0,
        'temperature_C': 18.5,
        'precipitation_mm': 0.0,
        'real_flow_pattern_ref': 75.0,
        'latitude': 37.4979,
        'longitude': 127.0276
    }])

# 3. Single Prediction Latency Benchmark (Batch Size = 1)
print("\n[3] Single-Prediction Latency (Live Dashboard Call Pattern, Batch Size = 1)")
print("-" * 80)
print("Testing single-call latency across 100 sequential requests...")

# Warm up
single_crowd_df = make_single_crowd_df()
for _ in range(10):
    crowd_model.predict(single_crowd_df)

crowd_latencies_ms = []
for _ in range(100):
    t_start = time.perf_counter()
    crowd_model.predict(single_crowd_df)
    t_end = time.perf_counter()
    crowd_latencies_ms.append((t_end - t_start) * 1000)

crowd_latencies_ms = np.array(crowd_latencies_ms)

print(f"\nCrowd Model (RandomForestRegressor, 200 trees, depth 20) Single Prediction Latency:")
print(f"  Mean Latency:   {crowd_latencies_ms.mean():.3f} ms")
print(f"  P50 (Median):   {np.median(crowd_latencies_ms):.3f} ms")
print(f"  P95 Latency:    {np.percentile(crowd_latencies_ms, 95):.3f} ms")
print(f"  P99 Latency:    {np.percentile(crowd_latencies_ms, 99):.3f} ms")
print(f"  Min / Max:      {crowd_latencies_ms.min():.3f} ms / {crowd_latencies_ms.max():.3f} ms")
print(f"  Single-Call Throughput: {1000.0 / crowd_latencies_ms.mean():.1f} predictions/sec")

# Delay Model Single Call
single_delay_df = make_single_delay_df()
for _ in range(10):
    delay_model.predict_proba(single_delay_df)

delay_latencies_ms = []
for _ in range(100):
    t_start = time.perf_counter()
    delay_model.predict_proba(single_delay_df)
    t_end = time.perf_counter()
    delay_latencies_ms.append((t_end - t_start) * 1000)

delay_latencies_ms = np.array(delay_latencies_ms)

print(f"\nDelay Model (RandomForestClassifier, 200 trees, depth 8) Single Prediction Latency:")
print(f"  Mean Latency:   {delay_latencies_ms.mean():.3f} ms")
print(f"  P50 (Median):   {np.median(delay_latencies_ms):.3f} ms")
print(f"  P95 Latency:    {np.percentile(delay_latencies_ms, 95):.3f} ms")
print(f"  P99 Latency:    {np.percentile(delay_latencies_ms, 99):.3f} ms")
print(f"  Min / Max:      {delay_latencies_ms.min():.3f} ms / {delay_latencies_ms.max():.3f} ms")
print(f"  Single-Call Throughput: {1000.0 / delay_latencies_ms.mean():.1f} predictions/sec")

# 4. Batch Prediction Throughput Benchmark
print("\n[4] Batch Prediction Throughput Benchmark (Realistic Multi-Station Batches)")
print("-" * 80)

batch_sizes = [1, 10, 131, 275, 1000, 5000]

print(f"{'Batch Size':<12} | {'Crowd Latency/Pred':<20} | {'Crowd Throughput':<18} | {'Delay Latency/Pred':<20} | {'Delay Throughput'}")
print("-" * 90)

for b_size in batch_sizes:
    # Build batch dataframe
    crowd_batch_df = pd.concat([single_crowd_df] * b_size, ignore_index=True)
    delay_batch_df = pd.concat([single_delay_df] * b_size, ignore_index=True)
    
    # Warmup
    crowd_model.predict(crowd_batch_df)
    delay_model.predict_proba(delay_batch_df)
    
    # Time crowd model batch
    n_iters = 10 if b_size < 1000 else 3
    t_crowd_total = 0.0
    for _ in range(n_iters):
        t_s = time.perf_counter()
        crowd_model.predict(crowd_batch_df)
        t_crowd_total += (time.perf_counter() - t_s)
    avg_crowd_total_ms = (t_crowd_total / n_iters) * 1000
    crowd_ms_per_pred = avg_crowd_total_ms / b_size
    crowd_throughput = b_size / (avg_crowd_total_ms / 1000.0)
    
    # Time delay model batch
    t_delay_total = 0.0
    for _ in range(n_iters):
        t_s = time.perf_counter()
        delay_model.predict_proba(delay_batch_df)
        t_delay_total += (time.perf_counter() - t_s)
    avg_delay_total_ms = (t_delay_total / n_iters) * 1000
    delay_ms_per_pred = avg_delay_total_ms / b_size
    delay_throughput = b_size / (avg_delay_total_ms / 1000.0)
    
    print(f"{b_size:<12} | {crowd_ms_per_pred:<8.4f} ms{'':<10} | {crowd_throughput:<8.1f} preds/s{'':<3} | {delay_ms_per_pred:<8.4f} ms{'':<10} | {delay_throughput:<8.1f} preds/s")

# 5. Analysis of the Original "test_model_features.py" Code
print("\n[5] AUDIT: Verification of README Claims (0.08ms and 12,500+ preds/sec)")
print("-" * 80)
# Replicate test_model_features.py exact batch benchmark: 275 requests
batch_275 = pd.concat([single_crowd_df] * 275, ignore_index=True)
t_start = time.perf_counter()
for _ in range(10):
    crowd_model.predict(batch_275)
t_elapsed_ms = ((time.perf_counter() - t_start) / 10) * 1000
amortized_ms = t_elapsed_ms / 275
throughput_275 = 275 / (t_elapsed_ms / 1000)

print(f"Replicating exact test_model_features.py test (Batch Size = 275):")
print(f"  Actual Measured Batch Total Time:      {t_elapsed_ms:.2f} ms")
print(f"  Actual Measured Amortized Latency:     {amortized_ms:.4f} ms/prediction")
print(f"  Actual Measured Batch Throughput:      {throughput_275:,.1f} predictions/sec")
print(f"  README Claimed Latency:                0.08 ms/prediction")
print(f"  README Claimed Throughput:             12,500+ predictions/sec")
print(f"  Single-Prediction Reality (Dashboard): {crowd_latencies_ms.mean():.3f} ms (NOT 0.08ms)")

print("\n" + "=" * 80)
