import os
import joblib
import numpy as np
import pandas as pd
from xgboost import XGBRegressor
from sklearn.ensemble import IsolationForest
from sklearn.cluster import KMeans
from sklearn.metrics import mean_absolute_error, mean_squared_error, r2_score

SAVED_MODELS_DIR = os.path.join(os.path.dirname(__file__), "saved_models")
PROCESSED_PARQUET = os.path.abspath(
    os.path.join(os.path.dirname(__file__), "..", "datasets", "processed", "master_bmrcl_ridership.parquet")
)
os.makedirs(SAVED_MODELS_DIR, exist_ok=True)


def train_bmrcl_ml_pipeline():
    if not os.path.exists(PROCESSED_PARQUET):
        raise FileNotFoundError(f"Clean BMRCL ridership dataset missing: {PROCESSED_PARQUET}")

    print(f"[ML Pipeline] Loading genuine BMRCL dataset from {PROCESSED_PARQUET}...")
    df = pd.read_parquet(PROCESSED_PARQUET)
    df["timestamp"] = pd.to_datetime(df["timestamp"])
    df = df.sort_values(by=["station_id", "timestamp"]).reset_index(drop=True)

    # Feature Engineering (Temporal & Lagged Features)
    df["hour"] = df["timestamp"].dt.hour
    df["day_of_week"] = df["timestamp"].dt.dayofweek
    df["is_weekend"] = (df["day_of_week"] >= 5).astype(int)
    df["demand"] = df["entries"].astype(float)

    # Lags within station group to strictly prevent leakage across stations
    print("[ML Pipeline] Engineering lag & rolling historical features...")
    df["lag_1h"] = df.groupby("station_id")["demand"].shift(1)
    df["lag_2h"] = df.groupby("station_id")["demand"].shift(2)
    df["rolling_mean_3h"] = df.groupby("station_id")["demand"].shift(1).rolling(window=3, min_periods=1).mean()
    df["rolling_max_3h"] = df.groupby("station_id")["demand"].shift(1).rolling(window=3, min_periods=1).max()

    # Targets for forecasting horizons
    df["target_1h"] = df.groupby("station_id")["demand"].shift(-1)
    df["target_2h"] = df.groupby("station_id")["demand"].shift(-2)
    df["target_4h"] = df.groupby("station_id")["demand"].shift(-4)

    # Drop edge rows with NaN from lags/targets
    df_clean = df.dropna(subset=["lag_1h", "lag_2h", "target_1h", "target_2h", "target_4h"]).copy()
    print(f"  -> Total usable sequential records after feature lag alignment: {len(df_clean):,}")

    feature_cols = [
        "station_id",
        "hour",
        "day_of_week",
        "is_weekend",
        "lag_1h",
        "lag_2h",
        "rolling_mean_3h",
        "rolling_max_3h"
    ]

    # Chronological Split (No temporal leakage): Train on Aug + early Sep, test on late Sep
    split_date = pd.to_datetime("2025-09-22 00:00:00")
    train_mask = df_clean["timestamp"] < split_date
    test_mask = df_clean["timestamp"] >= split_date

    X_train = df_clean.loc[train_mask, feature_cols]
    y_train_1h = df_clean.loc[train_mask, "target_1h"]
    y_train_2h = df_clean.loc[train_mask, "target_2h"]
    y_train_4h = df_clean.loc[train_mask, "target_4h"]

    X_test = df_clean.loc[test_mask, feature_cols]
    y_test_1h = df_clean.loc[test_mask, "target_1h"]
    y_test_2h = df_clean.loc[test_mask, "target_2h"]
    y_test_4h = df_clean.loc[test_mask, "target_4h"]

    print(f"  -> Chronological Train Records (Aug 1 - Sep 21): {len(X_train):,}")
    print(f"  -> Chronological Test Records (Sep 22 - Sep 30):  {len(X_test):,}")

    # Persistence baseline (predicted t+1h = current demand)
    persistence_preds = X_test["lag_1h"]
    persistence_mae = mean_absolute_error(y_test_1h, persistence_preds)
    persistence_r2 = r2_score(y_test_1h, persistence_preds)

    # 1. Demand Forecasting Model: XGBoost Regressors
    print("\n[Phase 12] Training XGBoost Multi-Horizon Models...")
    model_1h = XGBRegressor(n_estimators=140, max_depth=6, learning_rate=0.08, random_state=42)
    model_1h.fit(X_train, y_train_1h)
    preds_1h = model_1h.predict(X_test)
    mae_1h = mean_absolute_error(y_test_1h, preds_1h)
    rmse_1h = np.sqrt(mean_squared_error(y_test_1h, preds_1h))
    r2_1h = r2_score(y_test_1h, preds_1h)

    print(f"  -> Horizon +1h: MAE = {mae_1h:.2f} pax/hr, RMSE = {rmse_1h:.2f}, R² = {r2_1h:.3f} (vs Persistence MAE: {persistence_mae:.2f}, R²: {persistence_r2:.3f})")

    model_2h = XGBRegressor(n_estimators=140, max_depth=6, learning_rate=0.08, random_state=42)
    model_2h.fit(X_train, y_train_2h)
    preds_2h = model_2h.predict(X_test)
    mae_2h = mean_absolute_error(y_test_2h, preds_2h)
    rmse_2h = np.sqrt(mean_squared_error(y_test_2h, preds_2h))
    r2_2h = r2_score(y_test_2h, preds_2h)
    print(f"  -> Horizon +2h: MAE = {mae_2h:.2f} pax/hr, RMSE = {rmse_2h:.2f}, R² = {r2_2h:.3f}")

    model_4h = XGBRegressor(n_estimators=140, max_depth=6, learning_rate=0.08, random_state=42)
    model_4h.fit(X_train, y_train_4h)
    preds_4h = model_4h.predict(X_test)
    mae_4h = mean_absolute_error(y_test_4h, preds_4h)
    rmse_4h = np.sqrt(mean_squared_error(y_test_4h, preds_4h))
    r2_4h = r2_score(y_test_4h, preds_4h)
    print(f"  -> Horizon +4h: MAE = {mae_4h:.2f} pax/hr, RMSE = {rmse_4h:.2f}, R² = {r2_4h:.3f}")

    # Feature Importance (Explainable AI)
    feat_importance = dict(zip(feature_cols, [round(float(v), 4) for v in model_1h.feature_importances_]))
    print(f"\n[Phase 13] Feature Importances (XAI): {feat_importance}")

    # 2. Anomaly Detection: Isolation Forest
    print("\n[Phase 13] Training Isolation Forest for Real Anomaly Detection...")
    iso_features = ["hour", "day_of_week", "demand"]
    iso_forest = IsolationForest(n_estimators=120, contamination=0.03, random_state=42)
    iso_forest.fit(df_clean[iso_features])
    print("  -> Isolation Forest trained on genuine BMRCL demand vectors.")

    # 3. Station Pattern Analysis: KMeans Clustering on Peak Profiles
    print("\n[Phase 13] Performing Station Pattern Clustering...")
    station_hourly_matrix = df_clean.groupby(["station_id", "hour"])["demand"].mean().unstack(fill_value=0)
    kmeans = KMeans(n_clusters=3, random_state=42, n_init=10)
    station_clusters = kmeans.fit_predict(station_hourly_matrix)
    cluster_mapping = dict(zip(station_hourly_matrix.index, [int(c) for c in station_clusters]))
    # 0 = Commuter Suburban, 1 = High-Volume Tech Hub, 2 = Core City Interchange
    print(f"  -> Station Clusters identified across {len(cluster_mapping)} stations.")

    # Save artifacts
    forecaster_artifact = {
        "features": feature_cols,
        "model_1h": model_1h,
        "model_2h": model_2h,
        "model_4h": model_4h,
        "metrics": {
            "mae_1h": round(mae_1h, 2),
            "rmse_1h": round(rmse_1h, 2),
            "r2_1h": round(r2_1h, 3),
            "mae_2h": round(mae_2h, 2),
            "rmse_2h": round(rmse_2h, 2),
            "r2_2h": round(r2_2h, 3),
            "mae_4h": round(mae_4h, 2),
            "rmse_4h": round(rmse_4h, 2),
            "r2_4h": round(r2_4h, 3),
            "persistence_mae": round(persistence_mae, 2),
            "persistence_r2": round(persistence_r2, 3),
        },
        "feature_importances": feat_importance,
        "training_source": "BMRCL August + September 2025 RTI Data",
        "dataset_rows": len(df_clean)
    }

    joblib.dump(forecaster_artifact, os.path.join(SAVED_MODELS_DIR, "demand_forecaster.joblib"))
    joblib.dump(iso_forest, os.path.join(SAVED_MODELS_DIR, "isolation_forest.joblib"))
    joblib.dump(cluster_mapping, os.path.join(SAVED_MODELS_DIR, "station_clusters.joblib"))

    print("\n[ML Pipeline Complete] Successfully trained and saved BMRCL models:")
    print("  * demand_forecaster.joblib (XGBoost +1h, +2h, +4h)")
    print("  * isolation_forest.joblib (Isolation Forest Anomaly Detector)")
    print("  * station_clusters.joblib (KMeans Station Archetypes)")
    return forecaster_artifact


if __name__ == "__main__":
    train_bmrcl_ml_pipeline()
