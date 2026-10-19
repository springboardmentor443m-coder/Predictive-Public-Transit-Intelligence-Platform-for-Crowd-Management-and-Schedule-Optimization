
from pathlib import Path
from datetime import date, datetime

import joblib
import pandas as pd


# --------------------------------------------------
# PROJECT PATHS
# --------------------------------------------------

BASE_DIR = Path(__file__).resolve().parents[3]

MODEL_PATH = (
    BASE_DIR / "outputs" / "xgboost_demand_forecasting_model_v2.joblib"
)

FEATURE_PATH = (
    BASE_DIR / "outputs" / "demand_forecasting_feature_names_v2.joblib"
)

DATA_PATH = (
    BASE_DIR / "data" / "bmrcl" / "daily-ridership.csv"
)

STALE_DATA_THRESHOLD_DAYS = 3


# --------------------------------------------------
# LOAD TRAINED MODEL
# --------------------------------------------------

def load_demand_model():
    """Load the trained XGBoost model and its feature names."""

    if not MODEL_PATH.exists():
        raise FileNotFoundError(f"Demand model not found: {MODEL_PATH}")

    if not FEATURE_PATH.exists():
        raise FileNotFoundError(f"Feature file not found: {FEATURE_PATH}")

    return joblib.load(MODEL_PATH), joblib.load(FEATURE_PATH)


# --------------------------------------------------
# LOAD HISTORICAL RIDERSHIP
# --------------------------------------------------

def load_daily_ridership():
    """Load and validate available daily ridership records."""

    if not DATA_PATH.exists():
        raise FileNotFoundError(f"Dataset not found: {DATA_PATH}")

    df = pd.read_csv(DATA_PATH)

    required_columns = [
        "Record Date",
        "Total Smart Cards",
        "Total Tokens",
        "Total NCMC",
        "Group Ticket",
        "Total QR",
    ]

    missing_columns = [
        column for column in required_columns
        if column not in df.columns
    ]

    if missing_columns:
        raise ValueError(
            "Missing dataset columns: " + ", ".join(missing_columns)
        )

    df["Date"] = pd.to_datetime(
        df["Record Date"],
        dayfirst=True,
        errors="coerce",
    )

    ridership_columns = [
        "Total Smart Cards",
        "Total Tokens",
        "Total NCMC",
        "Group Ticket",
        "Total QR",
    ]

    for column in ridership_columns:
        df[column] = pd.to_numeric(df[column], errors="coerce")

    df["Ridership"] = df[ridership_columns].sum(
        axis=1,
        min_count=len(ridership_columns),
    )

    df = df.dropna(subset=["Date", "Ridership"])

    df = (
        df.sort_values("Date")
        .drop_duplicates(subset=["Date"], keep="last")
        .reset_index(drop=True)
    )

    if df.empty:
        raise ValueError("No valid daily ridership records are available.")

    df["Date"] = df["Date"].dt.normalize()

    return df[["Date", "Ridership"]].copy()


# --------------------------------------------------
# BUILD HISTORICAL FEATURES
# --------------------------------------------------

def build_forecasting_features(df):
    """
    Keep the existing row-based feature calculations.

    Missing calendar dates are not filled with invented ridership.
    """

    df = df.copy()

    df["Previous_Day_Ridership"] = df["Ridership"]
    df["Previous_Week_Ridership"] = df["Ridership"].shift(7)

    df["Rolling_7_Day_Avg"] = (
        df["Ridership"].rolling(window=7, min_periods=7).mean()
    )

    df["Demand_Change"] = df["Ridership"].diff()

    df["Rolling_3_Change"] = (
        df["Demand_Change"].rolling(window=3, min_periods=3).mean()
    )

    return df


# --------------------------------------------------
# DATA FRESHNESS
# --------------------------------------------------

def get_data_freshness(latest_date):
    today = pd.Timestamp(date.today()).normalize()
    latest_date = pd.Timestamp(latest_date).normalize()

    age_days = (today - latest_date).days

    if age_days < 0:
        status = "future_dated_observation"
    elif age_days > STALE_DATA_THRESHOLD_DAYS:
        status = "stale_historical_data"
    else:
        status = "recent_historical_data"

    return {
        "data_age_days": age_days,
        "is_stale": age_days > STALE_DATA_THRESHOLD_DAYS,
        "freshness_status": status,
        "stale_data_threshold_days": STALE_DATA_THRESHOLD_DAYS,
    }


# --------------------------------------------------
# PREDICT ONE FUTURE DAY
# --------------------------------------------------

def _predict_from_history(history, target_date, model, feature_names):
    """Generate one daily demand estimate from available history."""

    history = (
        history.copy()
        .sort_values("Date")
        .reset_index(drop=True)
    )

    features = build_forecasting_features(history)
    latest = features.iloc[-1]

    required_features = [
        "Previous_Day_Ridership",
        "Previous_Week_Ridership",
        "Rolling_7_Day_Avg",
        "Demand_Change",
        "Rolling_3_Change",
    ]

    missing_values = [
        name for name in required_features
        if pd.isna(latest[name])
    ]

    if missing_values:
        raise ValueError(
            "Insufficient historical data for forecasting: "
            + ", ".join(missing_values)
        )

    target_date = pd.Timestamp(target_date).normalize()

    input_data = {
        "Target_Day_of_Week": target_date.dayofweek,
        "Target_Day_of_Month": target_date.day,
        "Target_Month": target_date.month,
        "Target_Week_of_Year": float(target_date.isocalendar().week),
        "Target_Is_Weekend": int(target_date.dayofweek >= 5),
        "Previous_Day_Ridership": latest["Previous_Day_Ridership"],
        "Previous_Week_Ridership": latest["Previous_Week_Ridership"],
        "Rolling_7_Day_Avg": latest["Rolling_7_Day_Avg"],
        "Demand_Change": latest["Demand_Change"],
        "Rolling_3_Change": latest["Rolling_3_Change"],
    }

    missing_model_features = [
        name for name in feature_names
        if name not in input_data
    ]

    if missing_model_features:
        raise ValueError(
            "The saved model expects unsupported features: "
            + ", ".join(missing_model_features)
        )

    input_df = pd.DataFrame([input_data], columns=feature_names)
    prediction = float(model.predict(input_df)[0])

    if not pd.notna(prediction):
        raise ValueError("The model returned an invalid prediction.")

    return round(max(0.0, prediction), 2)


# --------------------------------------------------
# INTERNAL RECURSIVE FORECAST ENGINE
# --------------------------------------------------

def _generate_forecasts(target_date):
    """
    Generate daily estimates through target_date.

    Predicted values are appended recursively. Long-horizon errors
    may accumulate and have not been independently validated.
    """

    model, feature_names = load_demand_model()
    historical = load_daily_ridership()

    latest_date = pd.Timestamp(historical["Date"].max()).normalize()

    latest_count = float(
        historical.loc[
            historical["Date"] == latest_date, "Ridership"
        ].iloc[-1]
    )

    target_date = pd.Timestamp(target_date).normalize()

    if target_date <= latest_date:
        raise ValueError(
            f"Target date must be after the latest observed date "
            f"({latest_date:%Y-%m-%d})."
        )

    history = historical[["Date", "Ridership"]].copy()
    history["Date"] = pd.to_datetime(history["Date"]).dt.normalize()

    forecasts = []
    current_date = latest_date + pd.Timedelta(days=1)

    while current_date <= target_date:
        prediction = _predict_from_history(
            history=history,
            target_date=current_date,
            model=model,
            feature_names=feature_names,
        )

        forecasts.append({
            "date": current_date.strftime("%Y-%m-%d"),
            "predicted_ridership": prediction,
            "unit": "passengers",
            "is_observed_count": False,
        })

        history = pd.concat(
            [
                history,
                pd.DataFrame({
                    "Date": [current_date],
                    "Ridership": [prediction],
                }),
            ],
            ignore_index=True,
        )

        current_date += pd.Timedelta(days=1)

    freshness = get_data_freshness(latest_date)

    return {
        "latest_observed_date": latest_date.strftime("%Y-%m-%d"),
        "latest_observed_ridership": int(latest_count),
        "forecast_start_date": forecasts[0]["date"],
        "forecast_end_date": forecasts[-1]["date"],
        "forecast_horizon_days": len(forecasts),
        "forecasts": forecasts,
        "unit": "passengers",
        "model": "XGBoost",
        "model_version": "v2",
        "forecast_method": "recursive_multi_day_forecast",
        "data_status": "historical_data_forecast",
        "is_observed_count": False,
        "note": (
            "These are model-generated estimates, not observed or live "
            "passenger counts. Predictions are recursively used for "
            "subsequent days, so errors may accumulate. Long-horizon "
            "accuracy has not been independently validated."
        ),
        **freshness,
    }


# --------------------------------------------------
# EXISTING NEXT-DAY API COMPATIBILITY
# --------------------------------------------------

def predict_next_day_demand():
    historical = load_daily_ridership()
    latest_date = pd.Timestamp(historical["Date"].max()).normalize()

    result = _generate_forecasts(
        latest_date + pd.Timedelta(days=1)
    )

    first = result["forecasts"][0]

    return {
        "latest_observed_date": result["latest_observed_date"],
        "forecast_date": first["date"],
        "latest_observed_ridership": result["latest_observed_ridership"],
        "predicted_ridership": first["predicted_ridership"],
        "unit": "passengers",
        "model": result["model"],
        "model_version": result["model_version"],
        "forecast_type": "next_day_after_latest_observation",
        "is_observed_count": False,
        "data_status": result["data_status"],
        "data_age_days": result["data_age_days"],
        "is_stale": result["is_stale"],
        "freshness_status": result["freshness_status"],
        "stale_data_threshold_days": result["stale_data_threshold_days"],
        "note": result["note"],
    }


# --------------------------------------------------
# EXISTING 1, 7, OR 30-DAY FORECAST
# --------------------------------------------------

def predict_future_demand(days=7):
    if isinstance(days, bool) or not isinstance(days, int):
        raise ValueError("days must be an integer.")

    if days not in (1, 7, 30):
        raise ValueError("Supported forecast horizons are 1, 7, or 30 days.")

    historical = load_daily_ridership()
    latest_date = pd.Timestamp(historical["Date"].max()).normalize()

    return _generate_forecasts(
        latest_date + pd.Timedelta(days=days)
    )


# --------------------------------------------------
# NEW: FORECAST FOR ANY SPECIFIC FUTURE DATE
# --------------------------------------------------

def predict_demand_for_date(target_date):
    """
    Forecast a requested future date.

    Accepted formats:
      YYYY-MM-DD
      DD/MM/YYYY

    Example: 2026-10-15 or 15/10/2026.
    """

    if isinstance(target_date, str):
        try:
            if "/" in target_date:
                parsed_date = datetime.strptime(
                    target_date, "%d/%m/%Y"
                ).date()
            else:
                parsed_date = datetime.strptime(
                    target_date, "%Y-%m-%d"
                ).date()
        except ValueError as exc:
            raise ValueError(
                "Invalid date. Use YYYY-MM-DD or DD/MM/YYYY."
            ) from exc
    else:
        parsed_date = pd.Timestamp(target_date).date()

    result = _generate_forecasts(pd.Timestamp(parsed_date))
    target_text = parsed_date.strftime("%Y-%m-%d")

    selected_forecast = next(
        (
            item for item in result["forecasts"]
            if item["date"] == target_text
        ),
        None,
    )

    if selected_forecast is None:
        raise ValueError("The requested forecast date was not generated.")

    return {
        "target_date": target_text,
        "days_ahead_from_latest_observation": (
            parsed_date
            - pd.Timestamp(result["latest_observed_date"]).date()
        ).days,
        "latest_observed_date": result["latest_observed_date"],
        "latest_observed_ridership": result["latest_observed_ridership"],
        "forecast": selected_forecast,
        "unit": "passengers",
        "model": result["model"],
        "model_version": result["model_version"],
        "forecast_method": result["forecast_method"],
        "is_observed_count": False,
        "data_status": result["data_status"],
        "data_age_days": result["data_age_days"],
        "is_stale": result["is_stale"],
        "freshness_status": result["freshness_status"],
        "note": result["note"],
    }
