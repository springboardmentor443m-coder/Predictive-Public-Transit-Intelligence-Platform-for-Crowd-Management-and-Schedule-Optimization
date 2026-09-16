"""
train_model.py (v2 - real data)
Feature engineering + crowd prediction model for MetroFlow, trained on
REAL MTA subway ridership data (filtered to 12 major stations, see
data/metroflow_final.csv and the notebook history in the project README
for how this was sourced and cleaned).

Run: python train_model.py   (run from inside the model/ folder)
"""

import pandas as pd
import numpy as np
import joblib
from sklearn.ensemble import RandomForestRegressor
from sklearn.model_selection import train_test_split
from sklearn.metrics import mean_absolute_error, r2_score
from sklearn.preprocessing import LabelEncoder


def load_and_prepare(path="../data/metroflow_final.csv"):
    df = pd.read_csv(path)

    # --- feature engineering ---
    def time_bucket(hour):
        if 8 <= hour <= 10:
            return "morning_peak"
        elif 17 <= hour <= 19:
            return "evening_peak"
        elif 11 <= hour <= 16:
            return "midday"
        else:
            return "off_peak"

    df["time_bucket"] = df["hour"].apply(time_bucket)

    # encode categorical columns (station, day_of_week, time_bucket)
    station_encoder = LabelEncoder()
    day_encoder = LabelEncoder()
    bucket_encoder = LabelEncoder()

    df["station_encoded"] = station_encoder.fit_transform(df["station"])
    df["day_of_week_encoded"] = day_encoder.fit_transform(df["day_of_week"])
    df["time_bucket_encoded"] = bucket_encoder.fit_transform(df["time_bucket"])

    feature_cols = [
        "hour",
        "is_weekend",
        "is_holiday",
        "station_encoded",
        "day_of_week_encoded",
        "time_bucket_encoded",
    ]
    X = df[feature_cols]
    y = df["passenger_count"]

    return df, X, y, feature_cols, station_encoder, day_encoder, bucket_encoder


def main():
    df, X, y, feature_cols, station_encoder, day_encoder, bucket_encoder = load_and_prepare()

    X_train, X_test, y_train, y_test = train_test_split(
        X, y, test_size=0.2, random_state=42
    )

    baseline_pred = np.full_like(y_test, y_train.mean(), dtype=float)
    baseline_mae = mean_absolute_error(y_test, baseline_pred)

    model = RandomForestRegressor(
        n_estimators=200, max_depth=14, random_state=42, n_jobs=-1
    )
    model.fit(X_train, y_train)
    preds = model.predict(X_test)

    mae = mean_absolute_error(y_test, preds)
    r2 = r2_score(y_test, preds)

    print("=== Model evaluation (REAL data) ===")
    print(f"Baseline MAE (predict mean every time): {baseline_mae:.1f} passengers")
    print(f"Model MAE:                              {mae:.1f} passengers")
    print(f"Model R^2:                              {r2:.3f}")
    print(f"Improvement over baseline:               {100 * (1 - mae / baseline_mae):.1f}%")

    station_lookup = df[["station", "lat", "lon"]].drop_duplicates().reset_index(drop=True)

    joblib.dump(
        {
            "model": model,
            "feature_cols": feature_cols,
            "station_encoder": station_encoder,
            "day_encoder": day_encoder,
            "bucket_encoder": bucket_encoder,
            "station_lookup": station_lookup,
        },
        "metroflow_model.joblib",
    )
    print("\nSaved trained model -> metroflow_model.joblib")


if __name__ == "__main__":
    main()
