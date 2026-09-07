import pandas as pd
import numpy as np
import os
import joblib
from sklearn.ensemble import RandomForestRegressor
from sklearn.model_selection import train_test_split
from sklearn.metrics import mean_absolute_error, r2_score

DATA_PATH = os.path.join("data", "crowd_data.csv")
MODEL_DIR = "models"
MODEL_PATH = os.path.join(MODEL_DIR, "demand_forecast_model.pkl")

def train_demand_model():
    if not os.path.exists(DATA_PATH):
        print(f"Error: {DATA_PATH} not found.")
        return

    print("Loading raw dataset for clean training...")
    df = pd.read_csv(DATA_PATH, nrows=60000)

    # 1. Standardize columns
    df.columns = [c.strip().lower().replace(" ", "_") for c in df.columns]

    # 2. Identify datetime and entry columns
    time_col = next((c for c in df.columns if any(k in c for k in ['time', 'date', 'datetime', 'timestamp'])), None)
    entry_col = next((c for c in df.columns if any(k in c for k in ['entries', 'entry', 'inflow', 'board'])), 'entries')

    # 3. Clean target values (remove negative turnstile glitches and excessive spikes)
    df[entry_col] = pd.to_numeric(df[entry_col], errors='coerce').fillna(0)
    df = df[(df[entry_col] >= 0) & (df[entry_col] <= 12000)].copy()

    # 4. Feature Extraction: Hour & Day of Week
    if time_col and time_col in df.columns:
        parsed = pd.to_datetime(df[time_col], errors='coerce')
        df['hour'] = parsed.dt.hour
        df['day_of_week'] = parsed.dt.dayofweek
    else:
        df['hour'] = pd.to_numeric(df.get('hour', 8), errors='coerce')
        df['day_of_week'] = pd.to_numeric(df.get('day_of_week', 1), errors='coerce')

    # Fill any null values safely
    df['hour'] = df['hour'].fillna(8).astype(int)
    df['day_of_week'] = df['day_of_week'].fillna(1).astype(int)

    # 5. Define Features (X) and Target (y)
    X = df[['hour', 'day_of_week']]
    y = df[entry_col]

    # 6. Train/Test Split (80/20)
    X_train, X_test, y_train, y_test = train_test_split(X, y, test_size=0.20, random_state=42)

    print(f"Training Random Forest Regressor on {len(X_train)} samples...")
    model = RandomForestRegressor(n_estimators=100, max_depth=12, random_state=42, n_jobs=-1)
    model.fit(X_train, y_train)

    # 7. Evaluate Model Performance
    preds = model.predict(X_test)
    mae = mean_absolute_error(y_test, preds)
    r2 = r2_score(y_test, preds)
    print(f"Model Evaluation -> MAE: {mae:.2f} passengers | R2 Score: {r2:.2f}")

    # 8. Save Serialized Artifact
    os.makedirs(MODEL_DIR, exist_ok=True)
    joblib.dump(model, MODEL_PATH)
    print(f"Clean model successfully exported to {MODEL_PATH}")

if __name__ == "__main__":
    train_demand_model()