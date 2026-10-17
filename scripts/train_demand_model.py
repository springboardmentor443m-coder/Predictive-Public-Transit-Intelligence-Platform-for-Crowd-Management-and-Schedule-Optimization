"""
MetroFlow Phase 2: ML Demand Forecasting Pipeline
=================================================
Trains a Random Forest Regressor on the validated MetroFlow master dataset
to predict next-hour subway passenger demand per station complex.

Outputs:
  - metroflow/data/processed/feature_importance.csv
  - metroflow/data/processed/metroflow_demand_model.pkl
  - metroflow/data/processed/model_features.json
  - metroflow/data/processed/metroflow_features_df.csv (cached feature matrix)
"""

import os
import json
import joblib
import pandas as pd
import numpy as np
from sklearn.ensemble import RandomForestRegressor
from sklearn.metrics import mean_absolute_error, mean_squared_error, r2_score

# Paths
SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))
PROJECT_ROOT = os.path.abspath(os.path.join(SCRIPT_DIR, ".."))
DATA_DIR = os.path.join(PROJECT_ROOT, "data")
PROCESSED_DIR = os.path.join(DATA_DIR, "processed")
MASTER_CSV = os.path.join(PROCESSED_DIR, "metroflow_master.csv")

MODEL_PKL = os.path.join(PROCESSED_DIR, "metroflow_demand_model.pkl")
FEATURES_JSON = os.path.join(PROCESSED_DIR, "model_features.json")
IMPORTANCE_CSV = os.path.join(PROCESSED_DIR, "feature_importance.csv")

def log(msg):
    print(msg, flush=True)

def build_features(df):
    """Generates time, lag, and rolling features strictly without data leakage."""
    log("[FEATURE PIPELINE] Generating time-series features...")
    df = df.copy()
    df['transit_timestamp'] = pd.to_datetime(df['transit_timestamp'])
    df['station_complex_id'] = df['station_complex_id'].astype(str)
    
    # Sort chronologically per station
    df = df.sort_values(by=['station_complex_id', 'transit_timestamp']).reset_index(drop=True)
    
    # Time features
    df['hour'] = df['transit_timestamp'].dt.hour
    df['day_of_week'] = df['transit_timestamp'].dt.dayofweek
    df['month'] = df['transit_timestamp'].dt.month
    df['is_weekend'] = (df['day_of_week'] >= 5).astype(int)
    
    # Cyclical encodings
    df['hour_sin'] = np.sin(2 * np.pi * df['hour'] / 24.0)
    df['hour_cos'] = np.cos(2 * np.pi * df['hour'] / 24.0)
    df['dow_sin'] = np.sin(2 * np.pi * df['day_of_week'] / 7.0)
    df['dow_cos'] = np.cos(2 * np.pi * df['day_of_week'] / 7.0)
    
    # Group by station for lags & rolling
    grouped = df.groupby('station_complex_id')
    
    # Lags
    for lag in [1, 2, 3, 24, 168]:
        df[f'lag_{lag}h'] = grouped['passenger_count'].shift(lag)
        
    # Rolling features computed on lag_1h (past observations only, preventing leakage)
    df['rolling_mean_3h'] = grouped['lag_1h'].transform(lambda x: x.rolling(3, min_periods=1).mean())
    df['rolling_mean_24h'] = grouped['lag_1h'].transform(lambda x: x.rolling(24, min_periods=1).mean())
    df['rolling_mean_168h'] = grouped['lag_1h'].transform(lambda x: x.rolling(168, min_periods=1).mean())
    
    # Target variable: next-hour passenger demand for the same station
    df['target_next_hour'] = grouped['passenger_count'].shift(-1)
    
    # Drop rows with NaNs caused by initial lag window (168h) and final target shift
    df_clean = df.dropna(subset=['target_next_hour', 'lag_168h']).reset_index(drop=True)
    
    # One-hot encode stations for ML input while keeping original station_complex_id for tracking
    station_dummies = pd.get_dummies(df_clean['station_complex_id'], prefix='station', dtype=int)
    df_features = pd.concat([df_clean, station_dummies], axis=1)
    
    station_cols = station_dummies.columns.tolist()
    feature_cols = [
        'hour', 'day_of_week', 'month', 'is_weekend',
        'hour_sin', 'hour_cos', 'dow_sin', 'dow_cos',
        'lag_1h', 'lag_2h', 'lag_3h', 'lag_24h', 'lag_168h',
        'rolling_mean_3h', 'rolling_mean_24h', 'rolling_mean_168h',
        'transfers'
    ] + station_cols
    
    return df_features, feature_cols

def train_and_evaluate():
    log("=" * 60)
    log("STARTING METROFLOW ML DEMAND FORECASTING PIPELINE")
    log("=" * 60)
    
    log(f"[DATA] Loading processed master dataset from {MASTER_CSV}...")
    df_master = pd.read_csv(MASTER_CSV)
    
    df_features, feature_cols = build_features(df_master)
    log(f"[FEATURE PIPELINE] Feature matrix shape: {df_features.shape}")
    log(f"[FEATURE PIPELINE] Total features used ({len(feature_cols)}): {feature_cols}")
    
    # Chronological Time-Series Split (80% Train / 20% Test)
    # Sort strictly by timestamp across all stations to maintain temporal boundary
    df_sorted = df_features.sort_values(by='transit_timestamp').reset_index(drop=True)
    
    split_idx = int(len(df_sorted) * 0.8)
    train_df = df_sorted.iloc[:split_idx].copy()
    test_df = df_sorted.iloc[split_idx:].copy()
    
    X_train, y_train = train_df[feature_cols], train_df['target_next_hour']
    X_test, y_test = test_df[feature_cols], test_df['target_next_hour']
    
    log("\n" + "=" * 40)
    log("TIME-SERIES TRAIN / TEST SPLIT")
    log("=" * 40)
    log(f"Train rows: {len(train_df):,}")
    log(f"Test rows:  {len(test_df):,}")
    log(f"Train start timestamp: {train_df['transit_timestamp'].min()}")
    log(f"Train end timestamp:   {train_df['transit_timestamp'].max()}")
    log(f"Test start timestamp:  {test_df['transit_timestamp'].min()}")
    log(f"Test end timestamp:    {test_df['transit_timestamp'].max()}")
    
    # Train Random Forest Regressor
    log("\n[TRAINING] Fitting RandomForestRegressor (100 trees, max_depth=15)...")
    model = RandomForestRegressor(n_estimators=100, max_depth=15, random_state=42, n_jobs=-1)
    model.fit(X_train, y_train)
    log("[TRAINING] Model training complete!")
    
    # Evaluate
    y_pred = model.predict(X_test)
    test_df['predicted_next_hour'] = y_pred
    test_df['absolute_error'] = np.abs(test_df['target_next_hour'] - y_pred)
    
    mae = mean_absolute_error(y_test, y_pred)
    rmse = np.sqrt(mean_squared_error(y_test, y_pred))
    r2 = r2_score(y_test, y_pred)
    
    log("\n" + "=" * 40)
    log("MODEL EVALUATION METRICS")
    log("=" * 40)
    log(f"MAE:  {mae:.2f}")
    log(f"RMSE: {rmse:.2f}")
    log(f"R²:   {r2:.4f}")
    
    log("\n--- SAMPLE PREDICTIONS COMPARISON (TEST SET) ---")
    sample_view = test_df[['transit_timestamp', 'station_complex', 'target_next_hour', 'predicted_next_hour', 'absolute_error']].head(10)
    log(sample_view.to_string(index=False))
    
    # Feature Importances
    importances = model.feature_importances_
    fi_df = pd.DataFrame({
        'feature': feature_cols,
        'importance': importances
    }).sort_values(by='importance', ascending=False).reset_index(drop=True)
    
    log("\n--- TOP 15 FEATURE IMPORTANCES ---")
    log(fi_df.head(15).to_string(index=False))
    
    fi_df.to_csv(IMPORTANCE_CSV, index=False)
    log(f"[SAVED] {IMPORTANCE_CSV}")
    
    # Save Model & Feature List
    joblib.dump(model, MODEL_PKL)
    log(f"[SAVED] {MODEL_PKL}")
    
    with open(FEATURES_JSON, 'w') as f:
        json.dump(feature_cols, f, indent=2)
    log(f"[SAVED] {FEATURES_JSON}")
    
    # Save prepared dataset with predictions for crowd risk module
    all_pred = model.predict(df_sorted[feature_cols])
    df_sorted['predicted_next_hour'] = all_pred
    df_sorted['absolute_error'] = np.abs(df_sorted['target_next_hour'] - all_pred)
    
    cached_df_path = os.path.join(PROCESSED_DIR, "metroflow_features_df.csv")
    df_sorted.to_csv(cached_df_path, index=False)
    log(f"[SAVED] {cached_df_path}")
    
    return model, df_sorted, feature_cols, train_df, test_df, mae, rmse, r2, fi_df

if __name__ == "__main__":
    train_and_evaluate()
