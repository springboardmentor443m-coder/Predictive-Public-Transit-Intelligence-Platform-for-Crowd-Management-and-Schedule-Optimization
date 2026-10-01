import joblib
import pandas as pd


MODEL_PATH = "../outputs/xgboost_crowd_prediction_model.joblib"
ENCODER_PATH = "../outputs/station_encoder.joblib"


def load_prediction_model():
    model = joblib.load(MODEL_PATH)
    encoder = joblib.load(ENCODER_PATH)

    return model, encoder


def load_latest_station_data(station):
    entries_path = "../data/bmrcl/station-hourly.csv"
    exits_path = "../data/bmrcl/station-hourly-exits.csv"

    entries_df = pd.read_csv(
        entries_path,
        sep=";"
    )

    exits_df = pd.read_csv(
        exits_path,
        sep=";"
    )

    entries_df["Date"] = pd.to_datetime(
        entries_df["Date"]
    )

    exits_df["Date"] = pd.to_datetime(
        exits_df["Date"]
    )

    station_entries = entries_df[
        entries_df["Station"] == station
    ].copy()

    station_exits = exits_df[
        exits_df["Station"] == station
    ].copy()

    if station_entries.empty:
        return None

    latest_date = station_entries["Date"].max()

    latest_entries = station_entries[
        station_entries["Date"] == latest_date
    ].copy()

    latest_exits = station_exits[
        station_exits["Date"] == latest_date
    ].copy()

    latest_data = pd.merge(
        latest_entries,
        latest_exits,
        on=["Date", "Hour", "Station"],
        how="left",
        suffixes=("_entry", "_exit")
    )

    return latest_data.sort_values(
        "Hour"
    )


def build_prediction_features(station):
    latest_data = load_latest_station_data(station)

    if latest_data is None or latest_data.empty:
        return None

    latest_data["Net_Flow"] = (
        latest_data["Ridership_entry"]
        - latest_data["Ridership_exit"]
    )

    # Use the latest available hour
    latest_row = latest_data.iloc[-1]

    hour = int(latest_row["Hour"])
    date = latest_row["Date"]

    # Previous-hour data
    if len(latest_data) >= 2:
        previous_row = latest_data.iloc[-2]

        previous_hour_ridership = float(
            previous_row["Ridership_entry"]
        )

        previous_hour_exit = float(
            previous_row["Ridership_exit"]
        )

        previous_hour_net_flow = float(
            previous_row["Net_Flow"]
        )

    else:
        previous_hour_ridership = float(
            latest_row["Ridership_entry"]
        )

        previous_hour_exit = float(
            latest_row["Ridership_exit"]
        )

        previous_hour_net_flow = float(
            latest_row["Net_Flow"]
        )

    # Previous-day ridership
    entries_path = "../data/bmrcl/station-hourly.csv"

    entries_df = pd.read_csv(
        entries_path,
        sep=";"
    )

    entries_df["Date"] = pd.to_datetime(
        entries_df["Date"]
    )

    previous_day = date - pd.Timedelta(days=1)

    previous_day_data = entries_df[
        (entries_df["Station"] == station)
        & (entries_df["Date"] == previous_day)
        & (entries_df["Hour"] == hour)
    ]

    if previous_day_data.empty:
        previous_day_ridership = float(
            latest_row["Ridership_entry"]
        )
    else:
        previous_day_ridership = float(
            previous_day_data.iloc[0]["Ridership"]
        )

    # Rolling average of the previous 3 hours
    previous_ridership = latest_data[
        "Ridership_entry"
    ].iloc[:-1].tail(3)

    rolling_3h_avg = float(
        previous_ridership.mean()
    )

    return {
        "station": station,
        "hour": hour,
        "day_of_week": int(date.dayofweek),
        "day_of_month": int(date.day),
        "month": int(date.month),
        "is_weekend": int(date.dayofweek >= 5),
        "is_peak_hour": int(
            hour in [7, 8, 9, 17, 18, 19]
        ),
        "ridership_entry": float(
            latest_row["Ridership_entry"]
        ),
        "ridership_exit": float(
            latest_row["Ridership_exit"]
        ),
        "net_flow": float(
            latest_row["Net_Flow"]
        ),
        "previous_hour_ridership": previous_hour_ridership,
        "previous_day_ridership": previous_day_ridership,
        "rolling_3h_avg": rolling_3h_avg,
        "previous_hour_exit": previous_hour_exit,
        "previous_hour_net_flow": previous_hour_net_flow
    }


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
    previous_hour_net_flow
):
    model, encoder = load_prediction_model()

    # Create numerical input data
    input_df = pd.DataFrame([{
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
        "Previous_Hour_Net_Flow": previous_hour_net_flow
    }])

    # Encode station
    station_encoded = encoder.transform(
        pd.DataFrame({
            "Station": [station]
        })
    )

    station_feature_names = (
        encoder.get_feature_names_out(
            ["Station"]
        )
    )

    station_df = pd.DataFrame(
        station_encoded,
        columns=station_feature_names
    )

    # Combine numerical and station features
    input_df = pd.concat(
        [input_df, station_df],
        axis=1
    )

    # Make prediction
    prediction = model.predict(
        input_df
    )[0]

    return float(prediction)


def predict_from_latest_data(station):
    features = build_prediction_features(
        station
    )

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
        previous_hour_ridership=features[
            "previous_hour_ridership"
        ],
        previous_day_ridership=features[
            "previous_day_ridership"
        ],
        rolling_3h_avg=features[
            "rolling_3h_avg"
        ],
        previous_hour_exit=features[
            "previous_hour_exit"
        ],
        previous_hour_net_flow=features[
            "previous_hour_net_flow"
        ]
    )

    latest_data = load_latest_station_data(
        station
    )

    return {
        "station": station,
        "latest_date": str(
            latest_data["Date"].iloc[-1].date()
        ),
        "latest_hour": features["hour"],
        "predicted_next_hour_ridership": round(
            prediction,
            2
        )
    }