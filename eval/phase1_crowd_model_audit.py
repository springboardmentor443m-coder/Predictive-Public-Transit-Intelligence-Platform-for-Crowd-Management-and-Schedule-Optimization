import os
import sys
import glob
import sqlite3
import joblib
import numpy as np
import pandas as pd
from datetime import datetime
from sklearn.metrics import r2_score, mean_squared_error
from sklearn.model_selection import train_test_split

print("=" * 80)
print("METROFLOW AUDIT - PHASE 1: Crowd Prediction Model Verification")
print("=" * 80)

# 1. Search for training scripts and datasets
print("\n[1] AUDIT: Locating Training Scripts and Datasets")
print("-" * 80)

repo_root = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
parent_dir = os.path.abspath(os.path.join(repo_root, ".."))

training_script_patterns = [
    "**/train*.py", "**/*train*.ipynb", "**/crowd*.py", "**/crowd*.ipynb",
    "**/*rf*.py", "**/*regressor*.py"
]
found_scripts = []
for pat in training_script_patterns:
    found_scripts.extend(glob.glob(os.path.join(repo_root, pat), recursive=True))

found_scripts = [os.path.relpath(p, repo_root) for p in set(found_scripts) if "node_modules" not in p and ".git" not in p]
print(f"Candidate training/model scripts found in repository:")
for s in found_scripts:
    print(f"  - {s}")

# Check for dataset files
csv_files = glob.glob(os.path.join(repo_root, "**/*.csv"), recursive=True)
csv_files = [p for p in csv_files if "node_modules" not in p and ".git" not in p]
print(f"CSV datasets found in repository: {csv_files if csv_files else 'NONE (0 files)'}")

# Check parent directory for crowd model artifact and dataset
parent_pkl = os.path.join(parent_dir, "crowd_prediction_rf_compressed.pkl")
local_pkl = os.path.join(repo_root, "crowd_prediction_rf_compressed.pkl")
found_artifact = parent_pkl if os.path.exists(parent_pkl) else (local_pkl if os.path.exists(local_pkl) else None)

print(f"Crowd Regressor Model Artifact: {found_artifact}")
if found_artifact:
    artifact_size_mb = os.path.getsize(found_artifact) / (1024 * 1024)
    print(f"  Artifact File Size: {artifact_size_mb:.2f} MB")
else:
    print("  Artifact NOT found!")

# 2. Inspect Model Artifact Architecture and Parameters
print("\n[2] AUDIT: Model Artifact Inspection")
print("-" * 80)

if found_artifact:
    model = joblib.load(found_artifact)
    print(f"Model Class: {type(model).__name__}")
    print(f"Number of Estimators: {getattr(model, 'n_estimators', 'N/A')}")
    print(f"Max Depth: {getattr(model, 'max_depth', 'N/A')}")
    print(f"Min Samples Leaf: {getattr(model, 'min_samples_leaf', 'N/A')}")
    print(f"Criterion: {getattr(model, 'criterion', 'N/A')}")
    print(f"Bootstrap: {getattr(model, 'bootstrap', 'N/A')}")
    print(f"Random State: {getattr(model, 'random_state', 'N/A')}")
    print(f"OOB Score enabled: {getattr(model, 'oob_score', 'N/A')}")
    feature_names = list(getattr(model, 'feature_names_in_', []))
    print(f"Input Features ({len(feature_names)}): {feature_names}")
else:
    model = None

# 3. Database Data Examination (ridership_logs)
print("\n[3] AUDIT: Operational Database Ridership Records")
print("-" * 80)

db_path = os.path.join(repo_root, "backend", "metroflow.db")
if os.path.exists(db_path):
    conn = sqlite3.connect(db_path)
    cur = conn.cursor()
    cur.execute("SELECT COUNT(*) FROM ridership_logs")
    log_count = cur.fetchone()[0]
    cur.execute("SELECT MIN(timestamp), MAX(timestamp) FROM ridership_logs")
    min_ts, max_ts = cur.fetchone()
    cur.execute("SELECT COUNT(DISTINCT station_code) FROM ridership_logs")
    distinct_stations = cur.fetchone()[0]
    print(f"Database ridership_logs count: {log_count} rows")
    print(f"Time span: {min_ts} to {max_ts}")
    print(f"Distinct stations in logs: {distinct_stations}")
    
    # Check data generation provenance from seed.py
    print("Data provenance: According to backend/app/db/seed.py (line 303), these rows are")
    print("100% synthetically generated via a mathematical double-Gaussian curve generator.")
    
    # Load data for evaluation
    query = """
    SELECT r.station_code, r.timestamp, r.hour, r.day_of_week, r.is_weekend, r.inflow, r.outflow,
           s.line, s.latitude, s.longitude
    FROM ridership_logs r
    JOIN stations s ON r.station_code = s.station_code
    ORDER BY r.timestamp ASC
    """
    df = pd.read_sql_query(query, conn)
    conn.close()
    
    # Prepare features matching the model's 11 expected features
    import re
    def parse_line(line_str):
        nums = re.findall(r'\d+', str(line_str))
        return int(nums[0]) if nums else 2
        
    df['line_num'] = df['line'].apply(parse_line)
    df['dt'] = pd.to_datetime(df['timestamp'])
    df['year'] = df['dt'].dt.year
    df['month'] = df['dt'].dt.month
    df['is_morning_peak'] = ((df['hour'] >= 7) & (df['hour'] <= 9)).astype(int)
    df['is_evening_peak'] = ((df['hour'] >= 17) & (df['hour'] <= 19)).astype(int)
    
    # Convert station_code to int or hash
    def code_to_int(c):
        try:
            return int(c)
        except ValueError:
            return hash(str(c)) % 1000
    df['station_code_num'] = df['station_code'].apply(code_to_int)
    
    df['total_flow'] = df['inflow'] + df['outflow']
    
    X_db = df[['station_code_num', 'line_num', 'year', 'hour', 'day_of_week', 'is_weekend',
               'month', 'is_morning_peak', 'is_evening_peak', 'latitude', 'longitude']].rename(
                   columns={'station_code_num': 'station_code'}
               )
    y_db = df['total_flow']
    
    # Evaluate model predictions on DB data
    print("\n[4] AUDIT: Testing Model on Available DB Data (44,016 synthetic rows)")
    print("-" * 80)
    
    # Test random split (80/20)
    X_tr, X_te, y_tr, y_te = train_test_split(X_db, y_db, test_size=0.2, random_state=42)
    preds_random = model.predict(X_te)
    r2_random = r2_score(y_te, preds_random)
    rmse_random = np.sqrt(mean_squared_error(y_te, preds_random))
    print(f"Random 80/20 Split on DB data:")
    print(f"  R²:   {r2_random:.4f}")
    print(f"  RMSE: {rmse_random:.2f} (volume units)")
    
    # Test time-based split (first 80% dates train, last 20% dates test)
    split_idx = int(len(df) * 0.8)
    X_time_test = X_db.iloc[split_idx:]
    y_time_test = y_db.iloc[split_idx:]
    preds_time = model.predict(X_time_test)
    r2_time = r2_score(y_time_test, preds_time)
    rmse_time = np.sqrt(mean_squared_error(y_time_test, preds_time))
    print(f"\nTime-Based 80/20 Split (ordered chronologically by timestamp) on DB data:")
    print(f"  R²:   {r2_time:.4f}")
    print(f"  RMSE: {rmse_time:.2f} (volume units)")
    print(f"  Time test set range: {df['timestamp'].iloc[split_idx]} to {df['timestamp'].iloc[-1]}")
    
    # Compare raw scale of predictions vs targets
    print(f"\nTarget vs Prediction Statistics:")
    print(f"  Target `total_flow` mean:      {y_db.mean():.2f} (min: {y_db.min()}, max: {y_db.max()})")
    print(f"  Model predictions mean:        {preds_random.mean():.2f} (min: {preds_random.min():.2f}, max: {preds_random.max():.2f})")

print("\n" + "=" * 80)
print("PHASE 1 SUMMARY & VERIFICATION FINDINGS")
print("=" * 80)
