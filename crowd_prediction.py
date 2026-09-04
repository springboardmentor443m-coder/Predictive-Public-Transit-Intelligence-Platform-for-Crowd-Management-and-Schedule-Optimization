"""
MetroFlow - Crowd Prediction Starter Model
Starter ML implementation for passenger/crowd prediction.

This demo creates sample transportation data when no real dataset is available.
Replace the sample-data section with your actual passenger dataset later.
"""

import numpy as np
import pandas as pd
from sklearn.ensemble import RandomForestRegressor
from sklearn.model_selection import train_test_split
from sklearn.metrics import mean_absolute_error, r2_score


def create_sample_data(n=1000, random_state=42):
    rng = np.random.default_rng(random_state)

    hour = rng.integers(0, 24, n)
    day_of_week = rng.integers(0, 7, n)
    station_id = rng.integers(1, 11, n)
    is_weekend = (day_of_week >= 5).astype(int)

    # Synthetic passenger count with realistic peak-hour patterns.
    morning_peak = ((hour >= 7) & (hour <= 10)).astype(int)
    evening_peak = ((hour >= 17) & (hour <= 20)).astype(int)

    passengers = (
        80
        + station_id * 12
        + morning_peak * 180
        + evening_peak * 220
        + (1 - is_weekend) * 40
        + rng.normal(0, 35, n)
    )

    passengers = np.maximum(passengers, 10).round().astype(int)

    return pd.DataFrame({
        "hour": hour,
        "day_of_week": day_of_week,
        "station_id": station_id,
        "is_weekend": is_weekend,
        "passengers": passengers,
    })


def train_model(df):
    features = ["hour", "day_of_week", "station_id", "is_weekend"]
    X = df[features]
    y = df["passengers"]

    X_train, X_test, y_train, y_test = train_test_split(
        X, y, test_size=0.2, random_state=42
    )

    model = RandomForestRegressor(
        n_estimators=150,
        random_state=42,
        max_depth=10
    )
    model.fit(X_train, y_train)

    predictions = model.predict(X_test)

    print("Model Performance")
    print("-----------------")
    print(f"MAE: {mean_absolute_error(y_test, predictions):.2f}")
    print(f"R2 Score: {r2_score(y_test, predictions):.2f}")

    return model


def predict_crowd(model, hour, day_of_week, station_id):
    is_weekend = int(day_of_week >= 5)

    input_data = pd.DataFrame([{
        "hour": hour,
        "day_of_week": day_of_week,
        "station_id": station_id,
        "is_weekend": is_weekend,
    }])

    prediction = model.predict(input_data)[0]

    if prediction < 150:
        level = "Low"
    elif prediction < 300:
        level = "Medium"
    else:
        level = "High"

    return round(prediction), level


if __name__ == "__main__":
    data = create_sample_data()
    model = train_model(data)

    # Example: Monday, 18:00, Station 5
    passengers, level = predict_crowd(
        model=model,
        hour=18,
        day_of_week=0,
        station_id=5
    )

    print("\nExample Prediction")
    print("------------------")
    print(f"Predicted passengers: {passengers}")
    print(f"Crowd level: {level}")
