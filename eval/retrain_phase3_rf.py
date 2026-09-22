"""
MetroFlow Retrain Phase 3: Train and Evaluate Random Forest Regressors
File: eval/retrain_phase3_rf.py
Evaluates depth variations (max_depth=10, 15, 20) strictly on held-out time-based test set (1.2M rows).
"""

import os
import sys
import time
import joblib
import polars as pl
import numpy as np
from sklearn.ensemble import RandomForestRegressor
from sklearn.metrics import r2_score, mean_squared_error, mean_absolute_error

def run_phase3():
    print("=" * 80)
    print("METROFLOW RETRAIN - PHASE 3: RANDOM FOREST RETRAINING & VARIATIONS")
    print("=" * 80)
    
    t0 = time.time()
    print("[1/4] Loading pre-partitioned train and test Parquet datasets...")
    train_df = pl.read_parquet(r"eval\train_6m.parquet")
    test_df = pl.read_parquet(r"eval\test_6m.parquet")
    
    feature_cols = [
        "station_code", "line_num", "year", "hour", "day_of_week",
        "is_weekend", "month", "is_morning_peak", "is_evening_peak",
        "latitude", "longitude"
    ]
    target_col = "total_flow"
    
    X_train = train_df.select(feature_cols).to_numpy()
    y_train = train_df[target_col].to_numpy()
    
    X_test = test_df.select(feature_cols).to_numpy()
    y_test = test_df[target_col].to_numpy()
    
    print(f"  Training Matrix: {X_train.shape} ({train_df.shape[0]:,} rows)")
    print(f"  Held-Out Test Matrix: {X_test.shape} ({test_df.shape[0]:,} rows)")
    print(f"  Features ({len(feature_cols)}): {feature_cols}")
    print(f"  Target: '{target_col}' (Min: {y_test.min():.0f}, Mean: {y_test.mean():.2f}, Max: {y_test.max():.0f})")
    
    results = []
    
    # Model 1: Variation A (max_depth=10, n_estimators=20)
    print("\n" + "-" * 80)
    print("[2/4] Training Variation 1: max_depth=10, min_samples_leaf=5, n_estimators=20")
    print("-" * 80)
    t_start = time.time()
    rf_depth10 = RandomForestRegressor(
        n_estimators=20,
        max_depth=10,
        min_samples_leaf=5,
        n_jobs=-1,
        random_state=42
    )
    rf_depth10.fit(X_train, y_train)
    fit_time_10 = time.time() - t_start
    
    t_eval = time.time()
    y_pred_10 = rf_depth10.predict(X_test)
    eval_time_10 = time.time() - t_eval
    
    r2_10 = r2_score(y_test, y_pred_10)
    rmse_10 = np.sqrt(mean_squared_error(y_test, y_pred_10))
    mae_10 = mean_absolute_error(y_test, y_pred_10)
    print(f"  Fit Runtime:  {fit_time_10:.2f}s ({fit_time_10/60:.2f} min)")
    print(f"  Eval Runtime: {eval_time_10:.2f}s on 1.20M rows")
    print(f"  Test R^2:     {r2_10:.4f}")
    print(f"  Test RMSE:    {rmse_10:.2f}")
    print(f"  Test MAE:     {mae_10:.2f}")
    results.append({
        "model": "Variation 1 (max_depth=10, n_est=20)",
        "depth": 10,
        "n_est": 20,
        "fit_time_s": fit_time_10,
        "r2": r2_10,
        "rmse": rmse_10,
        "mae": mae_10
    })
    
    # Model 2: Variation B (max_depth=15, n_estimators=20)
    print("\n" + "-" * 80)
    print("[3/4] Training Variation 2: max_depth=15, min_samples_leaf=5, n_estimators=20")
    print("-" * 80)
    t_start = time.time()
    rf_depth15 = RandomForestRegressor(
        n_estimators=20,
        max_depth=15,
        min_samples_leaf=5,
        n_jobs=-1,
        random_state=42
    )
    rf_depth15.fit(X_train, y_train)
    fit_time_15 = time.time() - t_start
    
    t_eval = time.time()
    y_pred_15 = rf_depth15.predict(X_test)
    eval_time_15 = time.time() - t_eval
    
    r2_15 = r2_score(y_test, y_pred_15)
    rmse_15 = np.sqrt(mean_squared_error(y_test, y_pred_15))
    mae_15 = mean_absolute_error(y_test, y_pred_15)
    print(f"  Fit Runtime:  {fit_time_15:.2f}s ({fit_time_15/60:.2f} min)")
    print(f"  Eval Runtime: {eval_time_15:.2f}s on 1.20M rows")
    print(f"  Test R^2:     {r2_15:.4f}")
    print(f"  Test RMSE:    {rmse_15:.2f}")
    print(f"  Test MAE:     {mae_15:.2f}")
    results.append({
        "model": "Variation 2 (max_depth=15, n_est=20)",
        "depth": 15,
        "n_est": 20,
        "fit_time_s": fit_time_15,
        "r2": r2_15,
        "rmse": rmse_15,
        "mae": mae_15
    })
    
    # Model 3: Original Hyperparameters Baseline (max_depth=20, min_samples_leaf=5, n_estimators=50)
    print("\n" + "-" * 80)
    print("[4/4] Training Baseline Model: max_depth=20, min_samples_leaf=5, n_estimators=50")
    print("-" * 80)
    t_start = time.time()
    rf_depth20 = RandomForestRegressor(
        n_estimators=50,
        max_depth=20,
        min_samples_leaf=5,
        n_jobs=-1,
        random_state=42
    )
    rf_depth20.fit(X_train, y_train)
    fit_time_20 = time.time() - t_start
    
    t_eval = time.time()
    y_pred_20 = rf_depth20.predict(X_test)
    eval_time_20 = time.time() - t_eval
    
    r2_20 = r2_score(y_test, y_pred_20)
    rmse_20 = np.sqrt(mean_squared_error(y_test, y_pred_20))
    mae_20 = mean_absolute_error(y_test, y_pred_20)
    print(f"  Fit Runtime:  {fit_time_20:.2f}s ({fit_time_20/60:.2f} min)")
    print(f"  Eval Runtime: {eval_time_20:.2f}s on 1.20M rows")
    print(f"  Test R^2:     {r2_20:.4f}")
    print(f"  Test RMSE:    {rmse_20:.2f}")
    print(f"  Test MAE:     {mae_20:.2f}")
    results.append({
        "model": "Baseline Model (max_depth=20, n_est=50)",
        "depth": 20,
        "n_est": 50,
        "fit_time_s": fit_time_20,
        "r2": r2_20,
        "rmse": rmse_20,
        "mae": mae_20
    })
    
    # Save the best model
    best_model = rf_depth20
    out_model_path = r"eval\crowd_prediction_rf_retrained.pkl"
    print(f"\nSaving best retrained model to {out_model_path} (compressed joblib)...")
    # Attach feature names for scikit-learn validation
    best_model.feature_names_in_ = np.array(feature_cols, dtype=object)
    joblib.dump(best_model, out_model_path, compress=3)
    model_size_mb = os.path.getsize(out_model_path) / (1024 * 1024)
    print(f"Saved successfully: {model_size_mb:.2f} MB")
    
    print("\n" + "=" * 80)
    print("PHASE 3 RETRAINING SUMMARY TABLE (HELD-OUT TIME-BASED TEST SET):")
    print("=" * 80)
    print(f"{'Model Architecture':<40} | {'Test R^2':<10} | {'Test RMSE':<12} | {'Test MAE':<10} | {'Fit Time':<10}")
    print("-" * 90)
    for r in results:
        print(f"{r['model']:<40} | {r['r2']:<10.4f} | {r['rmse']:<12.2f} | {r['mae']:<10.2f} | {r['fit_time_s']:<8.1f}s")
    print("=" * 80)

if __name__ == "__main__":
    run_phase3()
