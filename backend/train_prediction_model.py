import json
from pathlib import Path
import joblib
import numpy as np
import pandas as pd

PROJECT_ROOT = Path(__file__).resolve().parent.parent
DATA_PATH = PROJECT_ROOT / "data" / "metroflow_processed_network.csv"
MODEL_DIR = PROJECT_ROOT / "backend" / "models"
MODEL_DIR.mkdir(parents=True, exist_ok=True)
MODEL_FILE = MODEL_DIR / "metroflow_demand_model.joblib"

print("--- 1. LOADING PROCESSED DATASET ---")
df = pd.read_csv(DATA_PATH)
df["timestamp"] = pd.to_datetime(df["timestamp"])
df.sort_values(by=["station_code", "timestamp"], inplace=True)
print(f"Total historical rows loaded: {len(df)}")

print("\n--- 2. FEATURE ENGINEERING (STEP D) ---")
df["lag_1h"] = df.groupby("station_code")["passenger_count"].shift(1)
df["lag_2h"] = df.groupby("station_code")["passenger_count"].shift(2)
df["rolling_3h"] = (
    df.groupby("station_code")["passenger_count"]
    .transform(lambda s: s.shift(1).rolling(3, min_periods=1).mean())
)

df["lag_1h"] = df["lag_1h"].fillna(df["passenger_count"])
df["lag_2h"] = df["lag_2h"].fillna(df["passenger_count"])
df["rolling_3h"] = df["rolling_3h"].fillna(df["passenger_count"])

feature_cols = [
    "hour",
    "day_of_week",
    "is_weekend",
    "is_peak_hour",
    "lag_1h",
    "lag_2h",
    "rolling_3h",
]

X = df[feature_cols].values.astype(np.float64)
y = df["passenger_count"].values.astype(np.float64)

# 80/20 train/test split
split_idx = int(len(df) * 0.8)
X_train, X_test = X[:split_idx], X[split_idx:]
y_train, y_test = y[:split_idx], y[split_idx:]

print(f"Training samples: {len(X_train)} | Testing samples: {len(X_test)}")

print("\n--- 3. ROBUST TRANSIT REGRESSOR TRAINING (STEP E) ---")
# Native OLS with L2 regularisation: (X^T X + alpha*I)^(-1) X^T y
# 100% bypasses Windows DLL AppControl blocks
X_train_bias = np.c_[np.ones(X_train.shape[0]), X_train]
X_test_bias = np.c_[np.ones(X_test.shape[0]), X_test]

alpha = 1.0
identity = np.eye(X_train_bias.shape[1])
identity[0, 0] = 0.0  # Do not regularize intercept

weights = np.linalg.solve(X_train_bias.T @ X_train_bias + alpha * identity, X_train_bias.T @ y_train)

# Evaluation
preds = X_test_bias @ weights
preds = np.clip(preds, a_min=0, a_max=None)

mae = float(np.mean(np.abs(y_test - preds)))
rmse = float(np.sqrt(np.mean((y_test - preds) ** 2)))
ss_tot = np.sum((y_test - np.mean(y_test)) ** 2)
ss_res = np.sum((y_test - preds) ** 2)
r2 = float(1.0 - (ss_res / ss_tot))

print(f"Mean Absolute Error (MAE): {mae:.2f} passengers")
print(f"Root Mean Squared Error (RMSE): {rmse:.2f} passengers")
print(f"R-squared Score (R2): {r2 * 100:.2f}% explained variance")

print("\n--- 4. SAVING TRAINED MODEL ARTIFACT ---")
artifact = {
    "weights": weights.tolist(),
    "feature_cols": feature_cols,
    "metrics": {
        "mae": round(mae, 2),
        "rmse": round(rmse, 2),
        "r2": round(r2, 4),
    },
}

with open(MODEL_FILE, "wb") as f:
    joblib.dump(artifact, f)

# Also dump a JSON copy for human readability
with open(MODEL_DIR / "metroflow_metrics.json", "w") as jf:
    json.dump(artifact["metrics"], jf, indent=2)

print(f"[SUCCESS] Model artifact saved to: {MODEL_FILE}")
print(f"[SUCCESS] Evaluation metrics written to: {MODEL_DIR / 'metroflow_metrics.json'}")