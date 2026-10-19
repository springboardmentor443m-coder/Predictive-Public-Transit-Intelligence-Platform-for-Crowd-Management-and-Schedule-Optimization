"""
Historical Delay Feature Generation

Creates historical schedule-based delay features from GTFS data.

This module does NOT invent realtime delays.
It uses the available static GTFS schedule information to create
historical schedule features that can later be used for prediction.
"""

from pathlib import Path
import pandas as pd
import numpy as np


# ============================================================
# PATHS
# ============================================================

PROJECT_ROOT = Path(__file__).resolve().parents[1]

STOP_TIMES_FILE = PROJECT_ROOT / "data" / "static" / "stop_times.txt"
TRIPS_FILE = PROJECT_ROOT / "data" / "static" / "trips.txt"
STOPS_FILE = PROJECT_ROOT / "data" / "static" / "stops.txt"

OUTPUT_FILE = (
    PROJECT_ROOT
    / "data"
    / "realtime"
    / "historical_delay_features.csv"
)


# ============================================================
# GTFS TIME CONVERSION
# ============================================================

def gtfs_time_to_seconds(value):
    """
    Convert GTFS HH:MM:SS time into seconds from service-day start.

    GTFS allows times beyond 24:00:00, for example:
        24:10:00
        25:23:00
        26:45:30
    """

    if pd.isna(value):
        return np.nan

    try:
        parts = str(value).strip().split(":")

        if len(parts) != 3:
            return np.nan

        hours = int(parts[0])
        minutes = int(parts[1])
        seconds = int(parts[2])

        return hours * 3600 + minutes * 60 + seconds

    except (ValueError, TypeError):
        return np.nan


# ============================================================
# LOAD GTFS DATA
# ============================================================

def load_data():

    print("Loading static GTFS stop times...")
    stop_times = pd.read_csv(
        STOP_TIMES_FILE,
        dtype=str
    )

    print(f"Stop times loaded: {len(stop_times)}")

    print("Loading static GTFS trips...")
    trips = pd.read_csv(
        TRIPS_FILE,
        dtype=str
    )

    print(f"Trips loaded: {len(trips)}")

    print("Loading static GTFS stops...")
    stops = pd.read_csv(
        STOPS_FILE,
        dtype=str
    )

    print(f"Stops loaded: {len(stops)}")

    return stop_times, trips, stops


# ============================================================
# CREATE HISTORICAL SCHEDULE FEATURES
# ============================================================

def create_historical_features(stop_times, trips, stops):

    print()
    print("========================================")
    print("HISTORICAL DELAY FEATURE GENERATION")
    print("========================================")

    df = stop_times.copy()

    # --------------------------------------------------------
    # Convert GTFS times
    # --------------------------------------------------------

    df["arrival_seconds"] = df["arrival_time"].apply(
        gtfs_time_to_seconds
    )

    df["departure_seconds"] = df["departure_time"].apply(
        gtfs_time_to_seconds
    )

    # --------------------------------------------------------
    # Remove unusable records
    # --------------------------------------------------------

    df = df.dropna(
        subset=[
            "arrival_seconds",
            "departure_seconds"
        ]
    ).copy()

    # --------------------------------------------------------
    # Convert sequence to numeric
    # --------------------------------------------------------

    df["stop_sequence"] = pd.to_numeric(
        df["stop_sequence"],
        errors="coerce"
    )

    # --------------------------------------------------------
    # Scheduled dwell time
    # --------------------------------------------------------

    df["scheduled_dwell_seconds"] = (
        df["departure_seconds"]
        - df["arrival_seconds"]
    )

    df["scheduled_dwell_seconds"] = (
        df["scheduled_dwell_seconds"]
        .clip(lower=0)
    )

    # --------------------------------------------------------
    # Scheduled travel time from previous stop
    # --------------------------------------------------------

    df = df.sort_values(
        ["trip_id", "stop_sequence"]
    ).copy()

    df["previous_stop_id"] = (
        df.groupby("trip_id")["stop_id"]
        .shift(1)
    )

    df["previous_arrival_seconds"] = (
        df.groupby("trip_id")["arrival_seconds"]
        .shift(1)
    )

    df["scheduled_travel_seconds"] = (
        df["arrival_seconds"]
        - df["previous_arrival_seconds"]
    )

    df["scheduled_travel_seconds"] = (
        df["scheduled_travel_seconds"]
        .where(
            df["previous_arrival_seconds"].notna()
        )
    )

    # --------------------------------------------------------
    # Trip progress
    # --------------------------------------------------------

    trip_stop_counts = (
        df.groupby("trip_id")["stop_sequence"]
        .max()
        .rename("trip_total_stops")
    )

    df = df.merge(
        trip_stop_counts,
        on="trip_id",
        how="left"
    )

    df["trip_progress_ratio"] = (
        df["stop_sequence"]
        / df["trip_total_stops"]
    )

    # --------------------------------------------------------
    # Time-of-day features
    # --------------------------------------------------------

    df["scheduled_hour"] = (
        df["arrival_seconds"] // 3600
    ).astype(int)

    df["scheduled_minute"] = (
        (df["arrival_seconds"] % 3600) // 60
    ).astype(int)

    df["scheduled_time_minutes"] = (
        df["arrival_seconds"] / 60
    )

    # --------------------------------------------------------
    # Service-day offset
    # --------------------------------------------------------

    df["service_day_offset"] = (
        df["arrival_seconds"] // 86400
    ).astype(int)

    # --------------------------------------------------------
    # Merge trip information
    # --------------------------------------------------------

    trip_columns = [
        column
        for column in [
            "trip_id",
            "route_id",
            "service_id",
            "direction_id",
            "shape_id"
        ]
        if column in trips.columns
    ]

    trip_info = trips[trip_columns].drop_duplicates(
        subset=["trip_id"]
    )

    df = df.merge(
        trip_info,
        on="trip_id",
        how="left"
    )

    # --------------------------------------------------------
    # Merge stop information
    # --------------------------------------------------------

    stop_columns = [
        column
        for column in [
            "stop_id",
            "stop_name",
            "stop_lat",
            "stop_lon"
        ]
        if column in stops.columns
    ]

    stop_info = stops[stop_columns].drop_duplicates(
        subset=["stop_id"]
    )

    df = df.merge(
        stop_info,
        on="stop_id",
        how="left"
    )

    # --------------------------------------------------------
    # Stop-level features
    # --------------------------------------------------------

    df["is_first_stop"] = (
        df["stop_sequence"] == 1
    )

    df["is_last_stop"] = (
        df["stop_sequence"] == df["trip_total_stops"]
    )

    # --------------------------------------------------------
    # Route-level schedule statistics
    # --------------------------------------------------------

    if "route_id" in df.columns:

        route_stats = (
            df.groupby("route_id")
            .agg(
                route_stop_observations=(
                    "stop_id",
                    "count"
                ),
                route_mean_travel_seconds=(
                    "scheduled_travel_seconds",
                    "mean"
                ),
                route_median_travel_seconds=(
                    "scheduled_travel_seconds",
                    "median"
                ),
                route_mean_dwell_seconds=(
                    "scheduled_dwell_seconds",
                    "mean"
                )
            )
            .reset_index()
        )

        df = df.merge(
            route_stats,
            on="route_id",
            how="left"
        )

    # --------------------------------------------------------
    # Stop-level schedule statistics
    # --------------------------------------------------------

    stop_stats = (
        df.groupby("stop_id")
        .agg(
            stop_observations=(
                "trip_id",
                "count"
            ),
            stop_mean_dwell_seconds=(
                "scheduled_dwell_seconds",
                "mean"
            ),
            stop_mean_travel_seconds=(
                "scheduled_travel_seconds",
                "mean"
            )
        )
        .reset_index()
    )

    df = df.merge(
        stop_stats,
        on="stop_id",
        how="left"
    )

    # --------------------------------------------------------
    # Clean numeric columns
    # --------------------------------------------------------

    numeric_columns = [
        "arrival_seconds",
        "departure_seconds",
        "scheduled_dwell_seconds",
        "scheduled_travel_seconds",
        "stop_sequence",
        "trip_total_stops",
        "trip_progress_ratio",
        "scheduled_hour",
        "scheduled_minute",
        "scheduled_time_minutes",
        "service_day_offset",
        "route_stop_observations",
        "route_mean_travel_seconds",
        "route_median_travel_seconds",
        "route_mean_dwell_seconds",
        "stop_observations",
        "stop_mean_dwell_seconds",
        "stop_mean_travel_seconds"
    ]

    for column in numeric_columns:

        if column in df.columns:

            df[column] = pd.to_numeric(
                df[column],
                errors="coerce"
            )

    # --------------------------------------------------------
    # Final ordering
    # --------------------------------------------------------

    preferred_columns = [
        "trip_id",
        "route_id",
        "service_id",
        "direction_id",
        "stop_id",
        "stop_name",
        "stop_sequence",
        "arrival_time",
        "departure_time",
        "arrival_seconds",
        "departure_seconds",
        "service_day_offset",
        "scheduled_hour",
        "scheduled_minute",
        "scheduled_time_minutes",
        "scheduled_dwell_seconds",
        "previous_stop_id",
        "scheduled_travel_seconds",
        "trip_total_stops",
        "trip_progress_ratio",
        "is_first_stop",
        "is_last_stop",
        "stop_observations",
        "stop_mean_dwell_seconds",
        "stop_mean_travel_seconds",
        "route_stop_observations",
        "route_mean_travel_seconds",
        "route_median_travel_seconds",
        "route_mean_dwell_seconds",
        "stop_lat",
        "stop_lon"
    ]

    available_columns = [
        column
        for column in preferred_columns
        if column in df.columns
    ]

    df = df[available_columns]

    return df


# ============================================================
# MAIN
# ============================================================

def main():

    print("========================================")
    print("HISTORICAL GTFS SCHEDULE FEATURES")
    print("========================================")

    stop_times, trips, stops = load_data()

    features = create_historical_features(
        stop_times,
        trips,
        stops
    )

    print()
    print("========================================")
    print("HISTORICAL FEATURE SUMMARY")
    print("========================================")

    print(
        f"Feature observations generated: {len(features)}"
    )

    if "route_id" in features.columns:

        print(
            f"Unique routes: "
            f"{features['route_id'].nunique()}"
        )

    if "trip_id" in features.columns:

        print(
            f"Unique trips: "
            f"{features['trip_id'].nunique()}"
        )

    if "stop_id" in features.columns:

        print(
            f"Unique stops: "
            f"{features['stop_id'].nunique()}"
        )

    print()
    print("Sample historical features:")

    print(
        features.head(10).to_string(
            index=False
        )
    )

    # --------------------------------------------------------
    # Save
    # --------------------------------------------------------

    OUTPUT_FILE.parent.mkdir(
        parents=True,
        exist_ok=True
    )

    features.to_csv(
        OUTPUT_FILE,
        index=False
    )

    print()
    print("Saved results to:")
    print(OUTPUT_FILE)

    print()
    print(
        "Historical delay feature generation "
        "completed successfully!"
    )


if __name__ == "__main__":
    main()