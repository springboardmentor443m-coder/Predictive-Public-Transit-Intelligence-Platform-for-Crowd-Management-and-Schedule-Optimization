
from functools import lru_cache
from pathlib import Path
import os

import joblib
import pandas as pd

# =========================================================
# PROJECT PATHS AND DEMO MODE
# =========================================================


PROJECT_ROOT = Path(__file__).resolve().parents[3]

MODEL_PATH = (
    PROJECT_ROOT
    / "outputs"
    / "xgboost_crowd_prediction_model_hourly_corrected.joblib"
)

ENCODER_PATH = (
    PROJECT_ROOT
    / "outputs"
    / "station_encoder.joblib"
)


DEMO_MODE_2026 = (
    os.getenv("AI_METROFLOW_DEMO_2026", "0").strip() == "1"
)

if DEMO_MODE_2026:
    ENTRIES_PATH = (
        PROJECT_ROOT / "data" / "bmrcl" / "demo_2026" / "station-hourly.csv"
    )
    EXITS_PATH = (
        PROJECT_ROOT / "data" / "bmrcl" / "demo_2026" / "station-hourly-exits.csv"
    )
else:
    ENTRIES_PATH = PROJECT_ROOT / "data" / "bmrcl" / "station-hourly.csv"
    EXITS_PATH = PROJECT_ROOT / "data" / "bmrcl" / "station-hourly-exits.csv"

PEAK_HOURS = [8, 9, 10, 17, 18, 19]

# Earliest eligible observation date for latest-data predictions.
# Earlier records remain available for historical lag calculations.
PREDICTION_START_DATE = pd.Timestamp("2025-08-12")


# =========================================================
# MODEL LOADING
# =========================================================

@lru_cache(maxsize=1)
def load_prediction_model():
    if not MODEL_PATH.exists():
        raise FileNotFoundError(
            f"Crowd prediction model not found: {MODEL_PATH}"
        )

    if not ENCODER_PATH.exists():
        raise FileNotFoundError(
            f"Station encoder not found: {ENCODER_PATH}"
        )

    return joblib.load(MODEL_PATH), joblib.load(ENCODER_PATH)


# =========================================================
# DATA LOADING
# =========================================================

def _load_dataset(path, label):
    if not path.exists():
        raise FileNotFoundError(
            f"{label} dataset not found: {path}"
        )

    df = pd.read_csv(path, sep=";")

    required = {"Date", "Hour", "Station", "Ridership"}
    missing = required - set(df.columns)

    if missing:
        raise ValueError(
            f"{label} dataset is missing columns: {sorted(missing)}"
        )

    df["Date"] = pd.to_datetime(df["Date"], errors="coerce")
    df["Hour"] = pd.to_numeric(df["Hour"], errors="coerce")
    df["Ridership"] = pd.to_numeric(df["Ridership"], errors="coerce")

    df = df.dropna(
        subset=["Date", "Hour", "Station", "Ridership"]
    ).copy()

    df["Date"] = df["Date"].dt.normalize()
    df["Hour"] = df["Hour"].astype(int)
    df = df[df["Hour"].between(0, 23)].copy()

    if df.duplicated(["Date", "Hour", "Station"]).any():
        raise ValueError(
            f"{label} dataset contains duplicate station-hour records."
        )

    return df


@lru_cache(maxsize=1)
def _load_entries_data():
    return _load_dataset(ENTRIES_PATH, "Entry")


@lru_cache(maxsize=1)
def _load_exits_data():
    return _load_dataset(EXITS_PATH, "Exit")


# =========================================================
# STATION NAME RESOLUTION
# =========================================================

def _normalize_station_name(name):
    return " ".join(
        str(name).casefold().replace(".", "").replace(",", "").split()
    )


@lru_cache(maxsize=1)
def _get_station_names():
    return sorted(
        _load_entries_data()["Station"]
        .dropna()
        .astype(str)
        .unique()
        .tolist()
    )


def resolve_station_name(station):
    if not isinstance(station, str) or not station.strip():
        return None

    requested = _normalize_station_name(station)
    stations = _get_station_names()

    exact = [
        name for name in stations
        if _normalize_station_name(name) == requested
    ]

    if len(exact) == 1:
        return exact[0]

    suffix = [
        name for name in stations
        if _normalize_station_name(name).endswith(" " + requested)
    ]

    if len(suffix) == 1:
        return suffix[0]

    if len(suffix) > 1:
        return None

    contains = [
        name for name in stations
        if requested in _normalize_station_name(name)
    ]

    return contains[0] if len(contains) == 1 else None


# =========================================================
# PREPARE STATION HISTORY
# =========================================================

@lru_cache(maxsize=100)
def _station_history(station):
    entries = _load_entries_data()
    exits = _load_exits_data()

    entries = entries.loc[
        entries["Station"] == station,
        ["Date", "Hour", "Station", "Ridership"],
    ].rename(columns={"Ridership": "Ridership_entry"})

    exits = exits.loc[
        exits["Station"] == station,
        ["Date", "Hour", "Station", "Ridership"],
    ].rename(columns={"Ridership": "Ridership_exit"})

    df = entries.merge(
        exits[["Date", "Hour", "Station", "Ridership_exit"]],
        on=["Date", "Hour", "Station"],
        how="left",
        validate="one_to_one",
    )

    df["Timestamp"] = (
        df["Date"] + pd.to_timedelta(df["Hour"], unit="h")
    )

    df = (
        df.sort_values("Timestamp")
        .drop_duplicates("Timestamp")
        .set_index("Timestamp")
    )

    if df.empty:
        return df.reset_index()

    # Build a continuous hourly timeline. Missing entry records remain
    # NaN rather than being invented or treated as zero passengers.
    hourly_index = pd.date_range(
        start=df.index.min(),
        end=df.index.max(),
        freq="h",
        name="Timestamp",
    )

    df = df.reindex(hourly_index)
    df.index.name = "Timestamp"

    df["Station"] = station
    df["Date"] = df.index.normalize()
    df["Hour"] = df.index.hour

    # An absent exit observation is not confirmed to mean zero exits.
    # Keep missing exits as NaN so affected feature rows can be excluded.
    df["Net_Flow"] = df["Ridership_entry"] - df["Ridership_exit"]

    # Because the timeline is hourly and continuous, shifts now represent
    # exact clock-hour intervals rather than previous available records.
    df["Previous_Hour_Ridership"] = df["Ridership_entry"].shift(1)
    df["Previous_Day_Ridership"] = df["Ridership_entry"].shift(24)

    df["Rolling_3H_Avg"] = (
        df["Ridership_entry"].shift(1).rolling(
            window=3, min_periods=3
        ).mean()
    )

    df["Previous_Hour_Exit"] = df["Ridership_exit"].shift(1)
    df["Previous_Hour_Net_Flow"] = df["Net_Flow"].shift(1)

    return df.reset_index()


def _features_from_row(station, row):
    required = [
        "Ridership_entry",
        "Ridership_exit",
        "Net_Flow",
        "Previous_Hour_Ridership",
        "Previous_Day_Ridership",
        "Rolling_3H_Avg",
        "Previous_Hour_Exit",
        "Previous_Hour_Net_Flow",
    ]

    if row[required].isna().any():
        return None

    timestamp = pd.Timestamp(row["Timestamp"])
    hour = int(timestamp.hour)

    return {
        "station": station,
        "latest_date": timestamp.strftime("%Y-%m-%d"),
        "hour": hour,
        "day_of_week": int(timestamp.dayofweek),
        "day_of_month": int(timestamp.day),
        "month": int(timestamp.month),
        "is_weekend": int(timestamp.dayofweek >= 5),
        "is_peak_hour": int(hour in PEAK_HOURS),
        "ridership_entry": float(row["Ridership_entry"]),
        "ridership_exit": float(row["Ridership_exit"]),
        "net_flow": float(row["Net_Flow"]),
        "previous_hour_ridership": float(row["Previous_Hour_Ridership"]),
        "previous_day_ridership": float(row["Previous_Day_Ridership"]),
        "rolling_3h_avg": float(row["Rolling_3H_Avg"]),
        "previous_hour_exit": float(row["Previous_Hour_Exit"]),
        "previous_hour_net_flow": float(row["Previous_Hour_Net_Flow"]),
    }


# =========================================================
# FEATURE BUILDERS
# =========================================================

def build_historical_prediction_features(station, selected_date, selected_hour):
    canonical = resolve_station_name(station)

    if canonical is None:
        return None

    try:
        selected_date = pd.Timestamp(selected_date).normalize()
        selected_hour = int(selected_hour)
    except (TypeError, ValueError):
        raise ValueError("Provide a valid date and hour.")

    if pd.isna(selected_date):
        raise ValueError("Provide a valid date.")

    if not 0 <= selected_hour <= 23:
        raise ValueError("selected_hour must be between 0 and 23.")

    history = _station_history(canonical)
    timestamp = selected_date + pd.Timedelta(hours=selected_hour)

    rows = history.loc[history["Timestamp"] == timestamp]

    if rows.empty:
        return None

    return _features_from_row(canonical, rows.iloc[0])


def build_prediction_features(station):
    canonical = resolve_station_name(station)

    if canonical is None:
        return None

    history = _station_history(canonical)

    if history.empty:
        return None

    required = [
        "Ridership_entry",
        "Ridership_exit",
        "Net_Flow",
        "Previous_Hour_Ridership",
        "Previous_Day_Ridership",
        "Rolling_3H_Avg",
        "Previous_Hour_Exit",
        "Previous_Hour_Net_Flow",
    ]

    # Calculate lag and rolling features using the complete history first.
    # Then restrict eligible prediction observations to the requested window.
    eligible_history = history.loc[
        history["Date"] >= PREDICTION_START_DATE
    ]
    valid = eligible_history.dropna(subset=required)

    if valid.empty:
        return None

    return _features_from_row(canonical, valid.iloc[-1])


# =========================================================
# MODEL PREDICTION
# =========================================================

def predict_next_hour_ridership(
    station,
    hour,
    day_of_week,
    day_of_month,
    month,
    is_weekend,
    is_peak_hour,
    ridership_entry,
    ridership_exit,
    net_flow,
    previous_hour_ridership,
    previous_day_ridership,
    rolling_3h_avg,
    previous_hour_exit,
    previous_hour_net_flow,
):
    model, encoder = load_prediction_model()
    canonical = resolve_station_name(station)

    if canonical is None:
        raise ValueError(
            f"Unknown or ambiguous station name: {station}"
        )

    numerical_features = {
        "Hour": hour,
        "Day_of_Week": day_of_week,
        "Day_of_Month": day_of_month,
        "Month": month,
        "Is_Weekend": is_weekend,
        "Is_Peak_Hour": is_peak_hour,
        "Ridership_entry": ridership_entry,
        "Ridership_exit": ridership_exit,
        "Net_Flow": net_flow,
        "Previous_Hour_Ridership": previous_hour_ridership,
        "Previous_Day_Ridership": previous_day_ridership,
        "Rolling_3H_Avg": rolling_3h_avg,
        "Previous_Hour_Exit": previous_hour_exit,
        "Previous_Hour_Net_Flow": previous_hour_net_flow,
    }

    input_df = pd.DataFrame([numerical_features])

    encoded = encoder.transform(
        pd.DataFrame({"Station": [canonical]})
    )

    station_columns = encoder.get_feature_names_out(["Station"])
    station_df = pd.DataFrame(encoded, columns=station_columns)

    input_df = pd.concat([input_df, station_df], axis=1)

    expected = list(model.feature_names_in_)
    missing = [name for name in expected if name not in input_df.columns]

    if missing:
        raise ValueError(
            "Prediction input is missing model features: "
            + ", ".join(missing)
        )

    input_df = input_df[expected]

    prediction = float(model.predict(input_df)[0])

    if not pd.notna(prediction):
        raise ValueError("The crowd model returned a non-finite prediction.")

    return max(0.0, prediction)


def predict_from_latest_data(station):
    canonical = resolve_station_name(station)

    if canonical is None:
        return None

    features = build_prediction_features(canonical)

    if features is None:
        return None

    prediction = predict_next_hour_ridership(
        station=features["station"],
        hour=features["hour"],
        day_of_week=features["day_of_week"],
        day_of_month=features["day_of_month"],
        month=features["month"],
        is_weekend=features["is_weekend"],
        is_peak_hour=features["is_peak_hour"],
        ridership_entry=features["ridership_entry"],
        ridership_exit=features["ridership_exit"],
        net_flow=features["net_flow"],
        previous_hour_ridership=features["previous_hour_ridership"],
        previous_day_ridership=features["previous_day_ridership"],
        rolling_3h_avg=features["rolling_3h_avg"],
        previous_hour_exit=features["previous_hour_exit"],
        previous_hour_net_flow=features["previous_hour_net_flow"],
    )

    return {
        "station": canonical,
        "latest_date": features["latest_date"],
        "latest_hour": features["hour"],
        "predicted_next_hour_ridership": round(prediction, 2),
        "prediction_target": "next_hour_ridership",
        "unit": "passengers",
        "data_mode": (
            "simulated_2026_demo"
            if DEMO_MODE_2026
            else "historical_dataset"
        ),
        "is_simulated_data": DEMO_MODE_2026,
        "is_live_data": False,
        "prediction_note": (
            "Model-generated estimate, not a live passenger count. "
            + (
                "Demo dates were shifted from historical data; they "
                "are not actual 2026 observations."
                if DEMO_MODE_2026
                else "The prediction uses the available historical dataset."
            )
        ),
    }


def load_latest_station_data(station):
    canonical = resolve_station_name(station)

    if canonical is None:
        return None

    history = _station_history(canonical)

    if history.empty:
        return None

    latest_date = history["Date"].max()
    result = history.loc[history["Date"] == latest_date].copy()

    return result.sort_values("Hour").reset_index(drop=True)


# =========================================================
# FUTURE DATE AND HOUR CROWD FORECASTING
# =========================================================

def predict_station_ridership_for_datetime(station, target_date, target_hour):
    """
    Forecast station-level ridership for a future date and hour.

    Demo mode uses date-shifted historical data, not actual 2026
    observations. Future entries are recursively estimated, while
    future exits use historical hourly medians.
    """

    canonical = resolve_station_name(station)

    if canonical is None:
        raise ValueError(
            f"Unknown or ambiguous station name: {station}"
        )

    try:
        target_date = pd.Timestamp(target_date).normalize()
        target_hour = int(target_hour)
    except (TypeError, ValueError):
        raise ValueError(
            "Provide a valid target date (YYYY-MM-DD) and hour (0-23)."
        )

    if pd.isna(target_date):
        raise ValueError("Provide a valid target date.")

    if not 0 <= target_hour <= 23:
        raise ValueError("target_hour must be between 0 and 23.")

    target_timestamp = target_date + pd.Timedelta(hours=target_hour)

    history = _station_history(canonical).copy()

    if history.empty:
        raise ValueError(f"No historical data found for {canonical}.")

    history = history.sort_values("Timestamp").reset_index(drop=True)

    required = [
        "Ridership_entry",
        "Ridership_exit",
        "Net_Flow",
        "Previous_Hour_Ridership",
        "Previous_Day_Ridership",
        "Rolling_3H_Avg",
        "Previous_Hour_Exit",
        "Previous_Hour_Net_Flow",
    ]

    # Keep pre-cutoff records for calculating historical features,
    # but select the forecast baseline from eligible observations.
    eligible_history = history.loc[
        history["Date"] >= PREDICTION_START_DATE
    ]
    valid = eligible_history.dropna(subset=required)

    if valid.empty:
        raise ValueError(
            "Not enough usable station observations on or after "
            f"{PREDICTION_START_DATE.date()} to forecast {canonical}."
        )

    latest = valid.iloc[-1]
    latest_timestamp = pd.Timestamp(latest["Timestamp"])

    if target_timestamp <= latest_timestamp:
        raise ValueError(
            "Target must be after the latest usable station observation "
            f"({latest_timestamp.strftime('%Y-%m-%d %H:%M')})."
        )

    steps = int(
        (target_timestamp - latest_timestamp).total_seconds() // 3600
    )

    if steps <= 0:
        raise ValueError("Target must be a future hour.")

    if steps > 24 * 90:
        raise ValueError(
            "Forecasts are limited to 90 days beyond the latest "
            "usable station observation."
        )

    exit_medians = (
        history.dropna(subset=["Ridership_exit"])
        .groupby("Hour")["Ridership_exit"]
        .median()
        .to_dict()
    )

    current_timestamp = latest_timestamp
    current_entry = float(latest["Ridership_entry"])
    current_exit = float(latest["Ridership_exit"])
    current_net_flow = float(latest["Net_Flow"])

    previous_entry = float(latest["Previous_Hour_Ridership"])
    previous_day_entry = float(latest["Previous_Day_Ridership"])
    previous_exit = float(latest["Previous_Hour_Exit"])
    previous_net_flow = float(latest["Previous_Hour_Net_Flow"])

    recent_entries = (
        history.loc[
            (history["Timestamp"] <= latest_timestamp),
            ["Timestamp", "Ridership_entry"],
        ]
        .dropna(subset=["Ridership_entry"])
        .tail(3)["Ridership_entry"]
        .astype(float)
        .tolist()
    )

    predicted_ridership = None

    for step in range(steps):
        if not recent_entries:
            raise ValueError(
                f"Insufficient recent entry history for {canonical}."
            )

        predicted_ridership = predict_next_hour_ridership(
            station=canonical,
            hour=int(current_timestamp.hour),
            day_of_week=int(current_timestamp.dayofweek),
            day_of_month=int(current_timestamp.day),
            month=int(current_timestamp.month),
            is_weekend=int(current_timestamp.dayofweek >= 5),
            is_peak_hour=int(current_timestamp.hour in PEAK_HOURS),
            ridership_entry=current_entry,
            ridership_exit=current_exit,
            net_flow=current_net_flow,
            previous_hour_ridership=previous_entry,
            previous_day_ridership=previous_day_entry,
            rolling_3h_avg=sum(recent_entries) / len(recent_entries),
            previous_hour_exit=previous_exit,
            previous_hour_net_flow=previous_net_flow,
        )

        predicted_ridership = max(0.0, float(predicted_ridership))
        next_timestamp = current_timestamp + pd.Timedelta(hours=1)

        if next_timestamp == target_timestamp:
            break

        estimated_exit = max(
            0.0,
            float(exit_medians.get(int(next_timestamp.hour), 0.0)),
        )

        previous_entry = current_entry
        previous_exit = current_exit
        previous_net_flow = current_net_flow

        prior_day_timestamp = next_timestamp - pd.Timedelta(days=1)
        prior_day_rows = history.loc[
            history["Timestamp"] == prior_day_timestamp
        ]

        if (
            not prior_day_rows.empty
            and pd.notna(prior_day_rows.iloc[0]["Ridership_entry"])
        ):
            previous_day_entry = float(
                prior_day_rows.iloc[0]["Ridership_entry"]
            )
        else:
            previous_day_entry = current_entry

        current_entry = predicted_ridership
        current_exit = estimated_exit
        current_net_flow = current_entry - current_exit

        recent_entries.append(current_entry)
        recent_entries = recent_entries[-3:]
        current_timestamp = next_timestamp

    return {
        "station": canonical,
        "target_datetime": target_timestamp.strftime("%Y-%m-%d %H:%M"),
        "target_date": target_timestamp.strftime("%Y-%m-%d"),
        "target_hour": target_hour,
        "predicted_ridership": round(float(predicted_ridership), 2),
        "unit": "passengers",
        "model": "XGBoost",
        "forecast_type": "recursive_future_hourly_station_forecast",
        "is_observed_count": False,
        "data_mode": (
            "simulated_2026_demo"
            if DEMO_MODE_2026
            else "historical_dataset"
        ),
        "is_simulated_data": DEMO_MODE_2026,
        "is_live_data": False,
        "data_status": (
            "simulated_demo_data_forecast"
            if DEMO_MODE_2026
            else "historical_data_forecast"
        ),
        "latest_station_observation": latest_timestamp.strftime(
            "%Y-%m-%d %H:%M"
        ),
        "forecast_steps": steps,
        "future_exit_method": "historical_hourly_median",
        "note": (
            (
                "SIMULATED DEMO: dates were shifted from historical data; "
                "these are not actual 2026 passenger observations. "
            )
            if DEMO_MODE_2026
            else ""
        )
        + (
            "Model-generated station-level estimate, not a live or "
            "observed count. Future exits are approximated using "
            "historical hourly medians. Recursive predictions can "
            "accumulate errors, especially over longer horizons."
        ),
    }
