
from functools import lru_cache
from pathlib import Path
from time import perf_counter
import logging

import pandas as pd

from app.services.prediction_service import (
    predict_from_latest_data,
    build_historical_prediction_features,
    predict_next_hour_ridership,
)

logger = logging.getLogger(__name__)

# ============================================================
# PATHS AND DATA LOADING
# ============================================================

BASE_DIR = Path(__file__).resolve().parents[3]

ENTRY_PATH = BASE_DIR / "data" / "bmrcl" / "station-hourly.csv"
EXIT_PATH = BASE_DIR / "data" / "bmrcl" / "station-hourly-exits.csv"

PEAK_HOURS = [7, 8, 9, 17, 18, 19]

PRESSURE_LEVELS = {
    "LOW": 0,
    "MODERATE": 0,
    "HIGH": 0,
    "CRITICAL": 0,
}


@lru_cache(maxsize=1)
def _load_flow_data() -> pd.DataFrame:
    """Load and cache combined historical station entry/exit data."""

    if not ENTRY_PATH.exists():
        raise FileNotFoundError(f"Entry data file not found: {ENTRY_PATH}")

    if not EXIT_PATH.exists():
        raise FileNotFoundError(f"Exit data file not found: {EXIT_PATH}")

    entries = pd.read_csv(ENTRY_PATH, sep=";")
    exits = pd.read_csv(EXIT_PATH, sep=";")

    required_columns = {"Date", "Hour", "Station", "Ridership"}

    for label, frame in (("entry", entries), ("exit", exits)):
        missing = required_columns - set(frame.columns)
        if missing:
            raise ValueError(
                f"The {label} dataset is missing columns: "
                + ", ".join(sorted(missing))
            )

    entries["Date"] = pd.to_datetime(entries["Date"], errors="coerce")
    exits["Date"] = pd.to_datetime(exits["Date"], errors="coerce")

    entries["Hour"] = pd.to_numeric(entries["Hour"], errors="coerce")
    exits["Hour"] = pd.to_numeric(exits["Hour"], errors="coerce")

    entries["Ridership"] = pd.to_numeric(
        entries["Ridership"], errors="coerce"
    )
    exits["Ridership"] = pd.to_numeric(
        exits["Ridership"], errors="coerce"
    )

    entries = entries.dropna(
        subset=["Date", "Hour", "Station"]
    ).copy()

    exits = exits.dropna(
        subset=["Date", "Hour", "Station"]
    ).copy()

    entries = entries.loc[
        entries["Hour"].between(0, 23)
    ].copy()
    exits = exits.loc[
        exits["Hour"].between(0, 23)
    ].copy()

    entries["Hour"] = entries["Hour"].astype(int)
    exits["Hour"] = exits["Hour"].astype(int)

    # Do not silently turn a missing entry observation into zero.
    # Missing exit records remain unknown in the merged data.
    entries = entries.rename(
        columns={"Ridership": "Ridership_entry"}
    )
    exits = exits.rename(
        columns={"Ridership": "Ridership_exit"}
    )

    df = entries.merge(
        exits[["Date", "Hour", "Station", "Ridership_exit"]],
        on=["Date", "Hour", "Station"],
        how="left",
        validate="one_to_one",
    )

    df["Ridership_entry"] = pd.to_numeric(
        df["Ridership_entry"], errors="coerce"
    )
    df["Ridership_exit"] = pd.to_numeric(
        df["Ridership_exit"], errors="coerce"
    )

    df["Net_Flow"] = (
        df["Ridership_entry"] - df["Ridership_exit"]
    )

    df["Is_Peak_Hour"] = df["Hour"].isin(PEAK_HOURS).astype(int)

    df["Timestamp"] = (
        df["Date"] + pd.to_timedelta(df["Hour"], unit="h")
    )

    df = df.dropna(
        subset=["Timestamp", "Station", "Ridership_entry"]
    )

    df = df.sort_values(
        ["Timestamp", "Station"]
    ).reset_index(drop=True)

    if df.empty:
        raise ValueError(
            "No valid historical monitoring records were loaded."
        )

    logger.info(
        "Loaded %s historical monitoring records across %s stations.",
        len(df),
        df["Station"].nunique(),
    )

    return df


# ============================================================
# CACHED NETWORK BENCHMARKS
# ============================================================

@lru_cache(maxsize=24)
def _get_hour_benchmarks(hour: int):
    """Cache network-wide historical benchmarks by hour."""

    df = _load_flow_data()

    current_rows = df.loc[df["Hour"] == hour]
    next_hour = (hour + 1) % 24
    next_rows = df.loc[df["Hour"] == next_hour]

    current_ridership = pd.to_numeric(
        current_rows["Ridership_entry"], errors="coerce"
    ).dropna()

    next_ridership = pd.to_numeric(
        next_rows["Ridership_entry"], errors="coerce"
    ).dropna()

    positive_net_flow = pd.to_numeric(
        current_rows["Net_Flow"], errors="coerce"
    ).clip(lower=0).dropna()

    all_ridership = pd.to_numeric(
        df["Ridership_entry"], errors="coerce"
    ).dropna()

    return {
        "current_ridership": current_ridership,
        "next_ridership": next_ridership,
        "positive_net_flow": positive_net_flow,
        "min_ridership": (
            float(all_ridership.min())
            if not all_ridership.empty
            else 0.0
        ),
        "max_ridership": (
            float(all_ridership.max())
            if not all_ridership.empty
            else 0.0
        ),
    }


def _percentile_rank(series: pd.Series, value: float) -> float:
    """Return the percentage of observations less than or equal to value."""

    if series.empty:
        return 0.0

    return max(
        0.0,
        min(float(series.le(value).mean() * 100), 100.0),
    )


def _absolute_demand_score(
    minimum: float,
    maximum: float,
    value: float,
) -> float:
    """Normalize ridership against the historical network-wide range."""

    if maximum == minimum:
        return 50.0

    score = ((float(value) - minimum) / (maximum - minimum)) * 100
    return max(0.0, min(score, 100.0))


def _pressure_level(score: float) -> str:
    """Convert an analytical pressure score into a monitoring level."""

    if score >= 85:
        return "CRITICAL"
    if score >= 60:
        return "HIGH"
    if score >= 30:
        return "MODERATE"
    return "LOW"


# ============================================================
# UNAVAILABLE STATION SNAPSHOT
# ============================================================

def _unavailable_snapshot(station, selected_date, selected_hour):
    """Represent a missing observation without inventing measurements."""

    normalized_date = (
        pd.Timestamp(selected_date).date()
        if selected_date is not None
        else None
    )

    return {
        "station": station,
        "monitoring_date": (
            str(normalized_date) if normalized_date is not None else None
        ),
        "monitoring_hour": (
            int(selected_hour) if selected_hour is not None else None
        ),
        "latest_date": (
            str(normalized_date) if normalized_date is not None else None
        ),
        "latest_hour": (
            int(selected_hour) if selected_hour is not None else None
        ),
        "current_ridership": None,
        "current_exit": None,
        "net_flow": None,
        "predicted_next_hour_ridership": None,
        "ml_predicted_next_hour_ridership": None,
        "observed_next_hour_ridership": None,
        "prediction_error": None,
        "prediction_error_percentage": None,
        "pressure_score": None,
        "congestion_level": "UNAVAILABLE",
        "peak_hour": (
            int(selected_hour) in PEAK_HOURS
            if selected_hour is not None
            else False
        ),
        "data_available": False,
        "prediction_available": False,
        "assessment_type": "historical-demand-pressure-replay",
    }


# ============================================================
# HISTORICAL ML PREDICTION
# ============================================================

def _predict_historical_demand(
    station,
    monitoring_date,
    monitoring_hour,
):
    """
    Predict using the trained model's existing feature definitions.

    Missing historical features produce no prediction. They are not
    replaced with fabricated lag values.
    """

    try:
        features = build_historical_prediction_features(
            station=station,
            selected_date=monitoring_date,
            selected_hour=monitoring_hour,
        )

        if features is None:
            logger.debug(
                "Historical prediction skipped: features unavailable "
                "for station=%s date=%s hour=%s",
                station,
                monitoring_date.date(),
                monitoring_hour,
            )
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

        if prediction is None or pd.isna(prediction):
            return None

        return max(0.0, float(prediction))

    except Exception:
        logger.exception(
            "Historical ML prediction failed for station=%s date=%s hour=%s",
            station,
            monitoring_date.date(),
            monitoring_hour,
        )
        return None


# ============================================================
# STATION SNAPSHOT
# ============================================================

def _station_snapshot(
    df: pd.DataFrame,
    station: str,
    selected_date=None,
    selected_hour=None,
    station_df=None,
):
    """Generate one station's monitoring snapshot."""

    station_started = perf_counter()

    if station_df is None:
        station_df = df.loc[df["Station"] == station].copy()
    else:
        station_df = station_df.copy()

    if station_df.empty:
        if selected_date is not None or selected_hour is not None:
            return _unavailable_snapshot(
                station, selected_date, selected_hour
            )
        return None

    station_df["Date"] = pd.to_datetime(
        station_df["Date"], errors="coerce"
    )

    if "Timestamp" not in station_df.columns:
        station_df["Timestamp"] = (
            station_df["Date"]
            + pd.to_timedelta(
                pd.to_numeric(station_df["Hour"], errors="coerce"),
                unit="h",
            )
        )
    else:
        station_df["Timestamp"] = pd.to_datetime(
            station_df["Timestamp"], errors="coerce"
        )

    if "Ridership_exit" not in station_df.columns:
        station_df["Ridership_exit"] = float("nan")

    if "Net_Flow" not in station_df.columns:
        station_df["Net_Flow"] = (
            pd.to_numeric(
                station_df["Ridership_entry"], errors="coerce"
            )
            - pd.to_numeric(
                station_df["Ridership_exit"], errors="coerce"
            )
        )

    if "Is_Peak_Hour" not in station_df.columns:
        station_df["Is_Peak_Hour"] = (
            station_df["Hour"].isin(PEAK_HOURS).astype(int)
        )

    station_df = station_df.sort_values(
        ["Date", "Hour"]
    ).reset_index(drop=True)

    replay_mode = (
        selected_date is not None or selected_hour is not None
    )

    selected_df = station_df

    if selected_date is not None:
        normalized_date = pd.Timestamp(selected_date).normalize()
        selected_df = selected_df.loc[
            selected_df["Date"].dt.normalize() == normalized_date
        ]

    if selected_hour is not None:
        selected_df = selected_df.loc[
            selected_df["Hour"] == int(selected_hour)
        ]

    if selected_df.empty:
        if replay_mode:
            return _unavailable_snapshot(
                station, selected_date, selected_hour
            )
        return None

    current = selected_df.iloc[-1]

    monitoring_date = pd.Timestamp(current["Date"])
    monitoring_hour = int(current["Hour"])

    current_entry_value = pd.to_numeric(
        pd.Series([current["Ridership_entry"]]), errors="coerce"
    ).iloc[0]

    if pd.isna(current_entry_value):
        if replay_mode:
            return _unavailable_snapshot(
                station, selected_date, selected_hour
            )
        return None

    current_ridership = max(0.0, float(current_entry_value))

    exit_value = pd.to_numeric(
        pd.Series([current["Ridership_exit"]]), errors="coerce"
    ).iloc[0]

    current_exit = (
        max(0.0, float(exit_value))
        if pd.notna(exit_value)
        else None
    )

    net_value = pd.to_numeric(
        pd.Series([current["Net_Flow"]]), errors="coerce"
    ).iloc[0]

    net_flow = float(net_value) if pd.notna(net_value) else None
    peak_hour = bool(current["Is_Peak_Hour"])

    current_timestamp = pd.Timestamp(current["Timestamp"])
    next_timestamp = current_timestamp + pd.Timedelta(hours=1)

    next_record = station_df.loc[
        station_df["Timestamp"] == next_timestamp
    ]

    observed_next_hour = None

    if not next_record.empty:
        observed_value = pd.to_numeric(
            pd.Series([next_record.iloc[0]["Ridership_entry"]]),
            errors="coerce",
        ).iloc[0]

        if pd.notna(observed_value):
            observed_next_hour = max(0.0, float(observed_value))

    # --------------------------------------------------------
    # ML PREDICTION
    # --------------------------------------------------------

    prediction_started = perf_counter()
    predicted_next_hour = None

    if replay_mode:
        predicted_next_hour = _predict_historical_demand(
            station=station,
            monitoring_date=monitoring_date,
            monitoring_hour=monitoring_hour,
        )
    else:
        try:
            prediction_result = predict_from_latest_data(station)

            if prediction_result:
                raw_prediction = prediction_result.get(
                    "predicted_next_hour_ridership"
                )

                if raw_prediction is not None and pd.notna(raw_prediction):
                    predicted_next_hour = max(
                        0.0, float(raw_prediction)
                    )

        except Exception:
            logger.exception(
                "Latest ML prediction failed for station=%s", station
            )

    logger.debug(
        "MONITORING PROFILE station=%s prediction=%.3fs",
        station,
        perf_counter() - prediction_started,
    )

    # --------------------------------------------------------
    # PREDICTION ERROR
    # --------------------------------------------------------

    prediction_error = None
    prediction_error_percentage = None

    if (
        replay_mode
        and predicted_next_hour is not None
        and observed_next_hour is not None
    ):
        prediction_error = predicted_next_hour - observed_next_hour

        if observed_next_hour != 0:
            prediction_error_percentage = (
                abs(prediction_error) / abs(observed_next_hour)
            ) * 100

    # --------------------------------------------------------
    # ANALYTICAL PRESSURE SCORING
    # --------------------------------------------------------

    benchmarks = _get_hour_benchmarks(monitoring_hour)

    current_rank = _percentile_rank(
        benchmarks["current_ridership"], current_ridership
    )

    net_flow_rank = (
        _percentile_rank(
            benchmarks["positive_net_flow"], max(net_flow, 0.0)
        )
        if net_flow is not None
        else None
    )

    current_absolute_score = _absolute_demand_score(
        benchmarks["min_ridership"],
        benchmarks["max_ridership"],
        current_ridership,
    )

    if predicted_next_hour is not None:
        predicted_rank = _percentile_rank(
            benchmarks["next_ridership"], predicted_next_hour
        )

        predicted_absolute_score = _absolute_demand_score(
            benchmarks["min_ridership"],
            benchmarks["max_ridership"],
            predicted_next_hour,
        )

        pressure_components = [
            (0.40, current_absolute_score),
            (0.25, predicted_absolute_score),
            (0.20, current_rank),
            (0.10, predicted_rank),
        ]

        if net_flow_rank is not None:
            pressure_components.append((0.05, net_flow_rank))

    else:
        # No predicted value is substituted. Renormalize the weights
        # of the current-observation components that are available.
        pressure_components = [
            (0.40, current_absolute_score),
            (0.20, current_rank),
        ]

        if net_flow_rank is not None:
            pressure_components.append((0.05, net_flow_rank))

    total_weight = sum(weight for weight, _ in pressure_components)

    pressure_score = (
        sum(weight * value for weight, value in pressure_components)
        / total_weight
        if total_weight > 0
        else None
    )

    if pressure_score is not None:
        pressure_score = max(
            0.0, min(float(pressure_score), 100.0)
        )
        congestion_level = _pressure_level(pressure_score)
    else:
        congestion_level = "UNAVAILABLE"

    logger.debug(
        "MONITORING PROFILE station=%s total=%.3fs",
        station,
        perf_counter() - station_started,
    )

    return {
        "station": station,
        "monitoring_date": str(monitoring_date.date()),
        "monitoring_hour": monitoring_hour,
        "latest_date": str(monitoring_date.date()),
        "latest_hour": monitoring_hour,
        "current_ridership": int(round(current_ridership)),
        "current_exit": (
            int(round(current_exit))
            if current_exit is not None
            else None
        ),
        "net_flow": (
            int(round(net_flow))
            if net_flow is not None
            else None
        ),
        "predicted_next_hour_ridership": (
            round(predicted_next_hour, 2)
            if predicted_next_hour is not None
            else None
        ),
        "ml_predicted_next_hour_ridership": (
            round(predicted_next_hour, 2)
            if predicted_next_hour is not None
            else None
        ),
        "observed_next_hour_ridership": (
            int(round(observed_next_hour))
            if observed_next_hour is not None
            else None
        ),
        "prediction_error": (
            round(prediction_error, 2)
            if prediction_error is not None
            else None
        ),
        "prediction_error_percentage": (
            round(prediction_error_percentage, 2)
            if prediction_error_percentage is not None
            else None
        ),
        "pressure_score": (
            round(pressure_score, 2)
            if pressure_score is not None
            else None
        ),
        "congestion_level": congestion_level,
        "peak_hour": peak_hour,
        "data_available": True,
        "prediction_available": predicted_next_hour is not None,
        "assessment_type": (
            "historical-demand-pressure-replay"
            if replay_mode
            else "latest-historical-demand-pressure"
        ),
    }


# ============================================================
# SINGLE-STATION API
# ============================================================

def get_station_monitoring(
    station: str,
    selected_date=None,
    selected_hour=None,
):
    """Return monitoring information for one station."""

    df = _load_flow_data()

    return _station_snapshot(
        df,
        station,
        selected_date=selected_date,
        selected_hour=selected_hour,
    )


# ============================================================
# NETWORK MONITORING
# ============================================================

def get_network_monitoring(
    selected_date=None,
    selected_hour=None,
):
    """Return network monitoring, including unavailable stations."""

    started = perf_counter()
    df = _load_flow_data()

    station_groups = {
        station: group
        for station, group in df.groupby("Station", sort=False)
    }

    # During replay, retain every station known to the historical data,
    # even if a station has no observation at the selected timestamp.
    snapshots = []

    for station in sorted(station_groups):
        snapshot = _station_snapshot(
            df,
            station,
            selected_date=selected_date,
            selected_hour=selected_hour,
            station_df=station_groups[station],
        )

        if snapshot is not None:
            snapshots.append(snapshot)

    elapsed = perf_counter() - started

    available_snapshots = [
        snapshot
        for snapshot in snapshots
        if snapshot.get("data_available", True)
        and snapshot.get("current_ridership") is not None
    ]

    unavailable_count = len(snapshots) - len(available_snapshots)

    logger.info(
        "MONITORING PROFILE stations=%d available=%d unavailable=%d "
        "total=%.3fs",
        len(snapshots),
        len(available_snapshots),
        unavailable_count,
        elapsed,
    )

    pressure_levels = dict(PRESSURE_LEVELS)

    for snapshot in available_snapshots:
        level = snapshot["congestion_level"]
        if level in pressure_levels:
            pressure_levels[level] += 1

    high_pressure_stations = sum(
        1
        for snapshot in available_snapshots
        if snapshot["congestion_level"] in ("HIGH", "CRITICAL")
    )

    highest_current = (
        max(
            available_snapshots,
            key=lambda item: item["current_ridership"],
        )
        if available_snapshots
        else None
    )

    predicted_snapshots = [
        snapshot
        for snapshot in available_snapshots
        if snapshot["predicted_next_hour_ridership"] is not None
    ]

    highest_predicted = (
        max(
            predicted_snapshots,
            key=lambda item: item["predicted_next_hour_ridership"],
        )
        if predicted_snapshots
        else None
    )

    if selected_date is not None:
        response_date = str(pd.Timestamp(selected_date).date())
    elif available_snapshots:
        response_date = available_snapshots[0]["monitoring_date"]
    else:
        response_date = None

    if selected_hour is not None:
        response_hour = int(selected_hour)
    elif available_snapshots:
        response_hour = available_snapshots[0]["monitoring_hour"]
    else:
        response_hour = None

    return {
        "stations_monitored": len(snapshots),
        "stations_available": len(available_snapshots),
        "stations_unavailable": unavailable_count,
        "monitoring_date": response_date,
        "monitoring_hour": response_hour,
        "pressure_levels": pressure_levels,
        "high_pressure_stations": high_pressure_stations,
        "highest_current_ridership": highest_current,
        "highest_predicted_ridership": highest_predicted,
        "station_snapshots": snapshots,
        "assessment_type": (
            "historical-demand-pressure-replay"
            if selected_date is not None or selected_hour is not None
            else "latest-historical-demand-pressure"
        ),
    }
