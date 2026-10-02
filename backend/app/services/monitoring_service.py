from pathlib import Path

import pandas as pd

from app.services.prediction_service import (
    predict_from_latest_data,
    build_historical_prediction_features,
    predict_next_hour_ridership,
)


# ============================================================
# PATHS
# ============================================================

BASE_DIR = Path(__file__).resolve().parents[3]

ENTRY_PATH = BASE_DIR / "data" / "bmrcl" / "station-hourly.csv"
EXIT_PATH = BASE_DIR / "data" / "bmrcl" / "station-hourly-exits.csv"


# ============================================================
# DATA LOADING
# ============================================================

def _load_flow_data() -> pd.DataFrame:
    """
    Load BMRCL station entry and exit data and combine them.
    """

    entries = pd.read_csv(
        ENTRY_PATH,
        sep=";"
    )

    exits = pd.read_csv(
        EXIT_PATH,
        sep=";"
    )

    entries["Date"] = pd.to_datetime(
        entries["Date"]
    )

    exits["Date"] = pd.to_datetime(
        exits["Date"]
    )

    entries = entries.rename(
        columns={
            "Ridership": "Ridership_entry"
        }
    )

    exits = exits.rename(
        columns={
            "Ridership": "Ridership_exit"
        }
    )

    df = entries.merge(
        exits,
        on=[
            "Date",
            "Hour",
            "Station"
        ],
        how="left"
    )

    df["Ridership_exit"] = (
        df["Ridership_exit"]
        .fillna(0)
    )

    df["Net_Flow"] = (
        df["Ridership_entry"]
        - df["Ridership_exit"]
    )

    df["Is_Peak_Hour"] = (
        df["Hour"].isin(
            [7, 8, 9, 17, 18, 19]
        ).astype(int)
    )

    return df


# ============================================================
# SCORING HELPERS
# ============================================================

def _percentile_rank(
    series: pd.Series,
    value: float
) -> float:
    """
    Return percentile rank of a value within a series.
    """

    values = pd.to_numeric(
        series,
        errors="coerce"
    ).dropna()

    if values.empty:
        return 0.0

    rank = (
        values.le(value).mean()
        * 100
    )

    return float(
        max(
            0.0,
            min(rank, 100.0)
        )
    )


def _absolute_demand_score(
    series: pd.Series,
    value: float
) -> float:
    """
    Convert an absolute ridership value into a 0-100
    score relative to the observed network range.
    """

    values = pd.to_numeric(
        series,
        errors="coerce"
    ).dropna()

    if values.empty:
        return 0.0

    minimum = float(
        values.min()
    )

    maximum = float(
        values.max()
    )

    if maximum == minimum:
        return 50.0

    score = (
        (value - minimum)
        / (maximum - minimum)
    ) * 100

    return float(
        max(
            0.0,
            min(score, 100.0)
        )
    )


def _pressure_level(
    score: float
) -> str:
    """
    Convert pressure score into a monitoring level.
    """

    if score >= 85:
        return "CRITICAL"

    if score >= 60:
        return "HIGH"

    if score >= 30:
        return "MODERATE"

    return "LOW"


# ============================================================
# STATION SNAPSHOT
# ============================================================

def _station_snapshot(
    df: pd.DataFrame,
    station: str,
    selected_date=None,
    selected_hour=None
):
    """
    Generate monitoring information for one station.

    Historical date/hour selections are treated as replay mode.
    Replay mode uses the trained ML model for prediction and
    compares that prediction with the actually observed
    next-hour ridership.
    """

    station_df = df[
        df["Station"] == station
    ].copy()

    if station_df.empty:
        return None

    station_df["Date"] = pd.to_datetime(
        station_df["Date"]
    )

    station_df = station_df.sort_values(
        ["Date", "Hour"]
    ).reset_index(drop=True)

    replay_mode = (
        selected_date is not None
        or selected_hour is not None
    )

    # ---------------------------------------------------------
    # Select monitoring record
    # ---------------------------------------------------------

    if selected_date is not None:
        selected_date = pd.Timestamp(
            selected_date
        ).normalize()

        station_df = station_df[
            station_df["Date"] == selected_date
        ]

    if selected_hour is not None:
        station_df = station_df[
            station_df["Hour"] == selected_hour
        ]

    if station_df.empty:
        return None

    current = station_df.iloc[-1]

    monitoring_date = pd.Timestamp(
        current["Date"]
    )

    monitoring_hour = int(
        current["Hour"]
    )

    current_ridership = max(
        0.0,
        float(
            current["Ridership_entry"]
        )
    )

    current_exit = max(
        0.0,
        float(
            current["Ridership_exit"]
        )
    )

    net_flow = float(
        current["Net_Flow"]
    )

    peak_hour = bool(
        current["Is_Peak_Hour"]
    )

    # ---------------------------------------------------------
    # Find actual next-hour observation
    # ---------------------------------------------------------

    full_station_df = df[
        df["Station"] == station
    ].copy()

    full_station_df["Date"] = pd.to_datetime(
        full_station_df["Date"]
    )

    full_station_df["Timestamp"] = (
        full_station_df["Date"]
        + pd.to_timedelta(
            full_station_df["Hour"],
            unit="h"
        )
    )

    current_timestamp = (
        monitoring_date
        + pd.Timedelta(
            hours=monitoring_hour
        )
    )

    next_timestamp = (
        current_timestamp
        + pd.Timedelta(hours=1)
    )

    next_record = full_station_df[
        full_station_df["Timestamp"]
        == next_timestamp
    ]

    if next_record.empty:
        observed_next_hour = None
    else:
        observed_next_hour = max(
            0.0,
            float(
                next_record.iloc[0]["Ridership_entry"]
            )
        )

    # ---------------------------------------------------------
    # Prediction / replay comparison
    # ---------------------------------------------------------

    predicted_next_hour = None

    if replay_mode:

        historical_features = (
            build_historical_prediction_features(
                station=station,
                selected_date=monitoring_date,
                selected_hour=monitoring_hour
            )
        )

        if historical_features is not None:

            try:

                raw_prediction = (
                    predict_next_hour_ridership(
                        station=historical_features[
                            "station"
                        ],
                        hour=historical_features[
                            "hour"
                        ],
                        day_of_week=historical_features[
                            "day_of_week"
                        ],
                        day_of_month=historical_features[
                            "day_of_month"
                        ],
                        month=historical_features[
                            "month"
                        ],
                        is_weekend=historical_features[
                            "is_weekend"
                        ],
                        is_peak_hour=historical_features[
                            "is_peak_hour"
                        ],
                        ridership_entry=historical_features[
                            "ridership_entry"
                        ],
                        ridership_exit=historical_features[
                            "ridership_exit"
                        ],
                        net_flow=historical_features[
                            "net_flow"
                        ],
                        previous_hour_ridership=historical_features[
                            "previous_hour_ridership"
                        ],
                        previous_day_ridership=historical_features[
                            "previous_day_ridership"
                        ],
                        rolling_3h_avg=historical_features[
                            "rolling_3h_avg"
                        ],
                        previous_hour_exit=historical_features[
                            "previous_hour_exit"
                        ],
                        previous_hour_net_flow=historical_features[
                            "previous_hour_net_flow"
                        ]
                    )
                )

                predicted_next_hour = max(
                    0.0,
                    float(raw_prediction)
                )

            except (
                TypeError,
                ValueError,
                KeyError
            ):

                predicted_next_hour = None

    else:

        prediction_result = (
            predict_from_latest_data(
                station
            )
        )

        if prediction_result:

            raw_prediction = (
                prediction_result.get(
                    "predicted_next_hour_ridership"
                )
            )

            if raw_prediction is not None:

                try:

                    predicted_next_hour = max(
                        0.0,
                        float(raw_prediction)
                    )

                except (
                    TypeError,
                    ValueError
                ):

                    predicted_next_hour = None

    # ---------------------------------------------------------
    # Prediction error
    # ---------------------------------------------------------

    prediction_error = None

    prediction_error_percentage = None

    if (
        replay_mode
        and predicted_next_hour is not None
        and observed_next_hour is not None
    ):

        prediction_error = (
            predicted_next_hour
            - observed_next_hour
        )

        if observed_next_hour != 0:

            prediction_error_percentage = (
                abs(prediction_error)
                / abs(observed_next_hour)
            ) * 100

    # ---------------------------------------------------------
    # Historical benchmark calculations
    # ---------------------------------------------------------

    current_hour_df = df[
        df["Hour"] == monitoring_hour
    ]

    next_hour = (
        monitoring_hour + 1
    ) % 24

    next_hour_df = df[
        df["Hour"] == next_hour
    ]

    current_rank = _percentile_rank(
        current_hour_df[
            "Ridership_entry"
        ],
        current_ridership
    )

    if predicted_next_hour is not None:

        predicted_rank = _percentile_rank(
            next_hour_df[
                "Ridership_entry"
            ],
            predicted_next_hour
        )

    else:

        predicted_rank = current_rank

    positive_net_flow = max(
        net_flow,
        0.0
    )

    net_flow_rank = _percentile_rank(
        current_hour_df[
            "Net_Flow"
        ].clip(lower=0),
        positive_net_flow
    )

    current_absolute_score = (
        _absolute_demand_score(
            df["Ridership_entry"],
            current_ridership
        )
    )

    if predicted_next_hour is not None:

        predicted_absolute_score = (
            _absolute_demand_score(
                df["Ridership_entry"],
                predicted_next_hour
            )
        )

    else:

        predicted_absolute_score = (
            current_absolute_score
        )

    # ---------------------------------------------------------
    # Pressure score
    # ---------------------------------------------------------

    pressure_score = (
        0.40 * current_absolute_score
        + 0.25 * predicted_absolute_score
        + 0.20 * current_rank
        + 0.10 * predicted_rank
        + 0.05 * net_flow_rank
    )

    pressure_score = float(
        max(
            0.0,
            min(
                pressure_score,
                100.0
            )
        )
    )

    congestion_level = _pressure_level(
        pressure_score
    )

    # ---------------------------------------------------------
    # Response
    # ---------------------------------------------------------

    return {
        "station": station,

        "monitoring_date": str(
            monitoring_date.date()
        ),

        "monitoring_hour": (
            monitoring_hour
        ),

        # Backward-compatible fields
        "latest_date": str(
            monitoring_date.date()
        ),

        "latest_hour": (
            monitoring_hour
        ),

        "current_ridership": int(
            round(current_ridership)
        ),

        "current_exit": int(
            round(current_exit)
        ),

        "net_flow": int(
            round(net_flow)
        ),

        "predicted_next_hour_ridership": (
            round(
                predicted_next_hour,
                2
            )
            if predicted_next_hour is not None
            else None
        ),

        "ml_predicted_next_hour_ridership": (
            round(
                predicted_next_hour,
                2
            )
            if predicted_next_hour is not None
            else None
        ),

        "observed_next_hour_ridership": (
            int(
                round(
                    observed_next_hour
                )
            )
            if observed_next_hour is not None
            else None
        ),

        "prediction_error": (
            round(
                prediction_error,
                2
            )
            if prediction_error is not None
            else None
        ),

        "prediction_error_percentage": (
            round(
                prediction_error_percentage,
                2
            )
            if prediction_error_percentage is not None
            else None
        ),

        "pressure_score": round(
            pressure_score,
            2
        ),

        "congestion_level": (
            congestion_level
        ),

        "peak_hour": (
            peak_hour
        ),

        "assessment_type": (
            "historical-demand-pressure-replay"
            if replay_mode
            else "latest-historical-demand-pressure"
        )
    }


# ============================================================
# SINGLE-STATION API SERVICE
# ============================================================

def get_station_monitoring(
    station: str,
    selected_date=None,
    selected_hour=None
):
    """
    Return monitoring information for one station.
    """

    df = _load_flow_data()

    return _station_snapshot(
        df,
        station,
        selected_date=selected_date,
        selected_hour=selected_hour
    )


# ============================================================
# NETWORK MONITORING
# ============================================================

def get_network_monitoring(
    selected_date=None,
    selected_hour=None
):
    """
    Return monitoring information for all stations.
    """

    df = _load_flow_data()

    stations = sorted(
        df["Station"]
        .dropna()
        .unique()
    )

    snapshots = []

    for station in stations:

        snapshot = _station_snapshot(
            df,
            station,
            selected_date=selected_date,
            selected_hour=selected_hour
        )

        if snapshot is not None:
            snapshots.append(
                snapshot
            )

    if not snapshots:

        return {
            "stations_monitored": 0,
            "monitoring_date": (
                str(selected_date)
                if selected_date is not None
                else None
            ),
            "monitoring_hour": (
                selected_hour
                if selected_hour is not None
                else None
            ),
            "pressure_levels": {},
            "high_pressure_stations": 0,
            "highest_current_ridership": None,
            "highest_predicted_ridership": None,
            "station_snapshots": [],
            "assessment_type": (
                "historical-demand-pressure-replay"
            )
        }

    # ---------------------------------------------------------
    # Pressure distribution
    # ---------------------------------------------------------

    pressure_levels = {}

    for snapshot in snapshots:

        level = snapshot[
            "congestion_level"
        ]

        pressure_levels[level] = (
            pressure_levels.get(
                level,
                0
            ) + 1
        )

    for level in [
        "LOW",
        "MODERATE",
        "HIGH",
        "CRITICAL"
    ]:

        pressure_levels.setdefault(
            level,
            0
        )

    # ---------------------------------------------------------
    # High-pressure stations
    # ---------------------------------------------------------

    high_pressure_stations = sum(
        1
        for snapshot in snapshots
        if snapshot[
            "congestion_level"
        ] in [
            "HIGH",
            "CRITICAL"
        ]
    )

    # ---------------------------------------------------------
    # Highest current ridership
    # ---------------------------------------------------------

    highest_current = max(
        snapshots,
        key=lambda x: x[
            "current_ridership"
        ]
    )

    # ---------------------------------------------------------
    # Highest predicted ridership
    # ---------------------------------------------------------

    predicted_snapshots = [
        snapshot
        for snapshot in snapshots
        if snapshot[
            "predicted_next_hour_ridership"
        ] is not None
    ]

    if predicted_snapshots:

        highest_predicted = max(
            predicted_snapshots,
            key=lambda x: x[
                "predicted_next_hour_ridership"
            ]
        )

    else:

        highest_predicted = None

    # ---------------------------------------------------------
    # Final response
    # ---------------------------------------------------------

    return {
        "stations_monitored": (
            len(snapshots)
        ),

        "monitoring_date": (
            snapshots[0][
                "monitoring_date"
            ]
        ),

        "monitoring_hour": (
            snapshots[0][
                "monitoring_hour"
            ]
        ),

        "pressure_levels": (
            pressure_levels
        ),

        "high_pressure_stations": (
            high_pressure_stations
        ),

        "highest_current_ridership": (
            highest_current
        ),

        "highest_predicted_ridership": (
            highest_predicted
        ),

        "station_snapshots": (
            snapshots
        ),

        "assessment_type": (
            "historical-demand-pressure-replay"
            if (
                selected_date is not None
                or selected_hour is not None
            )
            else "latest-historical-demand-pressure"
        )
    }