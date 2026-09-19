import os
import joblib
import pandas as pd
import psycopg2

from sklearn.ensemble import RandomForestRegressor
from sklearn.metrics import mean_absolute_error, mean_squared_error, r2_score


MODEL_PATH = "backend/app/ml/demand_model.joblib"


def load_data():
    conn = psycopg2.connect(
        dbname="metroflow_db"
    )

    query = """
        SELECT
            date_trunc('hour', transit_timestamp) AS timestamp,
            SUM(ridership) AS ridership
        FROM mta_hourly_ridership
        GROUP BY date_trunc('hour', transit_timestamp)
        ORDER BY timestamp;
    """

    df = pd.read_sql_query(query, conn)
    conn.close()

    return df


def prepare_features(df):
    df["timestamp"] = pd.to_datetime(df["timestamp"])

    df["hour"] = df["timestamp"].dt.hour
    df["day_of_week"] = df["timestamp"].dt.dayofweek
    df["day_of_year"] = df["timestamp"].dt.dayofyear
    df["month"] = df["timestamp"].dt.month

    df["lag_1"] = df["ridership"].shift(1)
    df["lag_24"] = df["ridership"].shift(24)
    df["lag_168"] = df["ridership"].shift(168)

    df = df.dropna().reset_index(drop=True)

    return df


def train_model():
    print("Loading MTA ridership data...")

    df = load_data()

    print(f"Hourly records: {len(df)}")

    df = prepare_features(df)

    features = [
        "hour",
        "day_of_week",
        "day_of_year",
        "month",
        "lag_1",
        "lag_24",
        "lag_168"
    ]

    X = df[features]
    y = df["ridership"]

    split_index = int(len(df) * 0.8)

    X_train = X.iloc[:split_index]
    X_test = X.iloc[split_index:]

    y_train = y.iloc[:split_index]
    y_test = y.iloc[split_index:]

    print(f"Training records: {len(X_train)}")
    print(f"Testing records: {len(X_test)}")

    model = RandomForestRegressor(
        n_estimators=100,
        max_depth=15,
        random_state=42,
        n_jobs=-1
    )

    print("Training demand forecasting model...")

    model.fit(X_train, y_train)

    predictions = model.predict(X_test)

    mae = mean_absolute_error(y_test, predictions)
    rmse = mean_squared_error(y_test, predictions) ** 0.5
    r2 = r2_score(y_test, predictions)

    print("\n===== DEMAND FORECASTING RESULTS =====")
    print(f"MAE  : {mae:.2f}")
    print(f"RMSE : {rmse:.2f}")
    print(f"R2   : {r2:.4f}")

    joblib.dump(
        {
            "model": model,
            "features": features
        },
        MODEL_PATH
    )

    print(f"\nModel saved to: {MODEL_PATH}")


if __name__ == "__main__":
    train_model()
