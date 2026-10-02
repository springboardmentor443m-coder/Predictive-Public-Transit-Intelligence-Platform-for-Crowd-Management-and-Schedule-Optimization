from pathlib import Path

import joblib
import pandas as pd


# Project root
BASE_DIR = Path(__file__).resolve().parents[3]

MODEL_PATH = (
    BASE_DIR
    / "outputs"
    / "xgboost_demand_forecasting_model_v2.joblib"
)

FEATURE_PATH = (
    BASE_DIR
    / "outputs"
    / "demand_forecasting_feature_names_v2.joblib"
)

DATA_PATH = (
    BASE_DIR
    / "data"
    / "bmrcl"
    / "daily-ridership.csv"
)


def load_demand_model():
    """Load the validated leakage-free demand forecasting model."""
    model = joblib.load(MODEL_PATH)
    feature_names = joblib.load(FEATURE_PATH)

    return model, feature_names


def load_daily_ridership():
    """Load and calculate total daily ridership."""

    df = pd.read_csv(DATA_PATH)

    df["Date"] = pd.to_datetime(
        df["Record Date"],
        dayfirst=True
    )

    df["Ridership"] = (
        df["Total Smart Cards"]
        + df["Total Tokens"]
        + df["Total NCMC"]
        + df["Group Ticket"]
        + df["Total QR"]
    )

    df = (
        df
        .sort_values("Date")
        .reset_index(drop=True)
    )

    return df


def build_forecasting_features(df):
    """
    Build features exactly as used during model training.

    These features use only information available
    before the target day.
    """

    df = df.copy()

    # Historical features
    df["Previous_Day_Ridership"] = df["Ridership"]

    df["Previous_Week_Ridership"] = (
        df["Ridership"].shift(7)
    )

    df["Rolling_7_Day_Avg"] = (
        df["Ridership"]
        .rolling(7)
        .mean()
    )

    df["Demand_Change"] = (
        df["Ridership"]
        - df["Ridership"].shift(1)
    )

    df["Rolling_3_Change"] = (
        df["Demand_Change"]
        .rolling(3)
        .mean()
    )

    return df


def predict_next_day_demand():
    """
    Predict ridership for the next calendar day
    using the latest available historical data.

    The target-day calendar features are generated
    from the next calendar date and do not use
    future ridership.
    """

    model, feature_names = load_demand_model()

    df = load_daily_ridership()

    df = build_forecasting_features(df)

    latest = df.iloc[-1]

    latest_date = latest["Date"]

    target_date = (
        latest_date
        + pd.Timedelta(days=1)
    )

    # Calendar information known in advance
    target_day_of_week = target_date.dayofweek
    target_day_of_month = target_date.day
    target_month = target_date.month
    target_week_of_year = (
        target_date.isocalendar().week
    )

    target_is_weekend = int(
        target_day_of_week >= 5
    )

    # Historical features
    input_data = {
        "Target_Day_of_Week": target_day_of_week,
        "Target_Day_of_Month": target_day_of_month,
        "Target_Month": target_month,
        "Target_Week_of_Year": float(
            target_week_of_year
        ),
        "Target_Is_Weekend": target_is_weekend,
        "Previous_Day_Ridership": latest[
            "Previous_Day_Ridership"
        ],
        "Previous_Week_Ridership": latest[
            "Previous_Week_Ridership"
        ],
        "Rolling_7_Day_Avg": latest[
            "Rolling_7_Day_Avg"
        ],
        "Demand_Change": latest[
            "Demand_Change"
        ],
        "Rolling_3_Change": latest[
            "Rolling_3_Change"
        ],
    }

    input_df = pd.DataFrame(
        [input_data],
        columns=feature_names
    )

    prediction = model.predict(input_df)[0]

    return {
        "latest_date": str(
            latest_date.date()
        ),
        "target_date": str(
            target_date.date()
        ),
        "latest_ridership": int(
            latest["Ridership"]
        ),
        "predicted_demand": round(
            float(prediction),
            2
        ),
        "unit": "passengers",
        "model": "XGBoost",
        "model_version": "v2",
        "forecast_type": "next_calendar_day",
    }