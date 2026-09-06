import os
import sys
import pandas as pd


# ============================================================
# CONFIGURATION
# ============================================================

INPUT_FILE = os.path.join(
    "data",
    "realtime",
    "historical_delay_features.csv"
)

OUTPUT_DIR = os.path.join(
    "data",
    "crowd"
)

OUTPUT_FILE = os.path.join(
    OUTPUT_DIR,
    "crowd_management_features.csv"
)


# ============================================================
# CROWD / SERVICE INTENSITY DEFINITIONS
# ============================================================

PEAK_HOURS = {
    7, 8, 9,
    16, 17, 18, 19
}


# ============================================================
# MAIN
# ============================================================

def main():

    print("=" * 60)
    print("V/LINE CROWD MANAGEMENT FEATURE GENERATION")
    print("=" * 60)

    # --------------------------------------------------------
    # Load historical schedule features
    # --------------------------------------------------------

    print("\nLoading historical schedule features...")

    if not os.path.exists(INPUT_FILE):

        print("\nERROR: Input file not found:")
        print(INPUT_FILE)

        sys.exit(1)

    df = pd.read_csv(INPUT_FILE)

    print(f"Rows loaded: {len(df)}")
    print(f"Columns loaded: {len(df.columns)}")

    # --------------------------------------------------------
    # Required columns
    # --------------------------------------------------------

    required_columns = [
        "trip_id",
        "route_id",
        "stop_id",
        "stop_name",
        "stop_sequence",
        "scheduled_hour",
        "trip_total_stops",
        "trip_progress_ratio",
        "is_first_stop",
        "is_last_stop",
        "stop_observations",
        "route_stop_observations",
        "route_mean_travel_seconds",
        "route_median_travel_seconds",
        "route_mean_dwell_seconds",
        "stop_mean_dwell_seconds",
        "stop_mean_travel_seconds",
        "stop_lat",
        "stop_lon"
    ]

    missing_columns = [
        column
        for column in required_columns
        if column not in df.columns
    ]

    if missing_columns:

        print("\nERROR: Required columns are missing:")

        for column in missing_columns:
            print(f"  {column}")

        sys.exit(1)

    # --------------------------------------------------------
    # Numeric conversion
    # --------------------------------------------------------

    numeric_columns = [
        "scheduled_hour",
        "stop_sequence",
        "trip_total_stops",
        "trip_progress_ratio",
        "stop_observations",
        "route_stop_observations",
        "route_mean_travel_seconds",
        "route_median_travel_seconds",
        "route_mean_dwell_seconds",
        "stop_mean_dwell_seconds",
        "stop_mean_travel_seconds",
        "stop_lat",
        "stop_lon"
    ]

    for column in numeric_columns:

        df[column] = pd.to_numeric(
            df[column],
            errors="coerce"
        )

    # --------------------------------------------------------
    # Feature generation
    # --------------------------------------------------------

    print("\nGenerating crowd-management features...")

    # Peak period indicator
    df["is_peak_hour"] = (
        df["scheduled_hour"].isin(PEAK_HOURS)
    )

    # Peak-period category
    df["peak_period"] = "OFF_PEAK"

    df.loc[
        df["scheduled_hour"].isin({7, 8, 9}),
        "peak_period"
    ] = "MORNING_PEAK"

    df.loc[
        df["scheduled_hour"].isin({16, 17, 18, 19}),
        "peak_period"
    ] = "EVENING_PEAK"

    # --------------------------------------------------------
    # Stop service intensity
    # --------------------------------------------------------

    df["stop_service_intensity"] = (
        df["stop_observations"]
        .fillna(0)
    )

    # --------------------------------------------------------
    # Route-stop service intensity
    # --------------------------------------------------------

    df["route_stop_service_intensity"] = (
        df["route_stop_observations"]
        .fillna(0)
    )

    # --------------------------------------------------------
    # Relative stop importance
    # --------------------------------------------------------

    df["stop_position_ratio"] = (
        df["trip_progress_ratio"]
        .clip(lower=0, upper=1)
    )

    # --------------------------------------------------------
    # Operational stop indicator
    # --------------------------------------------------------

    df["is_intermediate_stop"] = (
        (~df["is_first_stop"].astype(bool))
        &
        (~df["is_last_stop"].astype(bool))
    )

    # --------------------------------------------------------
    # Scheduled dwell indicator
    # --------------------------------------------------------

    df["scheduled_dwell_indicator"] = (
        df["stop_mean_dwell_seconds"]
        .fillna(0)
    )

    # --------------------------------------------------------
    # Scheduled travel intensity
    # --------------------------------------------------------

    df["route_travel_intensity"] = (
        df["route_mean_travel_seconds"]
        .fillna(
            df["route_median_travel_seconds"]
        )
    )

    # --------------------------------------------------------
    # Stop activity category
    # --------------------------------------------------------

    df["stop_activity_category"] = "LOW"

    df.loc[
        df["stop_observations"] >= 500,
        "stop_activity_category"
    ] = "MEDIUM"

    df.loc[
        df["stop_observations"] >= 2000,
        "stop_activity_category"
    ] = "HIGH"

    # --------------------------------------------------------
    # Route service category
    # --------------------------------------------------------

    route_counts = (
        df.groupby("route_id")["trip_id"]
        .nunique()
        .rename("route_trip_count")
        .reset_index()
    )

    df = df.merge(
        route_counts,
        on="route_id",
        how="left"
    )

    df["route_service_category"] = "LOW"

    df.loc[
        df["route_trip_count"] >= 100,
        "route_service_category"
    ] = "MEDIUM"

    df.loc[
        df["route_trip_count"] >= 500,
        "route_service_category"
    ] = "HIGH"

    # --------------------------------------------------------
    # Hourly route service frequency
    # --------------------------------------------------------

    hourly_frequency = (
        df.groupby(
            ["route_id", "scheduled_hour"]
        )["trip_id"]
        .nunique()
        .rename("hourly_route_trip_frequency")
        .reset_index()
    )

    df = df.merge(
        hourly_frequency,
        on=["route_id", "scheduled_hour"],
        how="left"
    )

    # --------------------------------------------------------
    # Hourly stop service frequency
    # --------------------------------------------------------

    stop_frequency = (
        df.groupby(
            ["stop_id", "scheduled_hour"]
        )["trip_id"]
        .nunique()
        .rename("hourly_stop_trip_frequency")
        .reset_index()
    )

    df = df.merge(
        stop_frequency,
        on=["stop_id", "scheduled_hour"],
        how="left"
    )

    # --------------------------------------------------------
    # Route-level peak indicator
    # --------------------------------------------------------

    df["route_peak_service"] = (
        (
            df["is_peak_hour"]
            &
            (
                df["hourly_route_trip_frequency"]
                >= df["hourly_route_trip_frequency"].median()
            )
        )
    )

    # --------------------------------------------------------
    # Crowd pressure proxy
    # --------------------------------------------------------
    #
    # IMPORTANT:
    # This is NOT passenger occupancy.
    #
    # It represents schedule/service pressure using:
    #   - peak period
    #   - stop activity
    #   - route frequency
    #
    # It must not be described as actual passenger counts.
    #

    df["service_pressure_score"] = (
        df["stop_observations"].fillna(0)
        .rank(pct=True)
        +
        df["hourly_stop_trip_frequency"].fillna(0)
        .rank(pct=True)
        +
        df["hourly_route_trip_frequency"].fillna(0)
        .rank(pct=True)
    ) / 3.0

    # --------------------------------------------------------
    # Service pressure category
    # --------------------------------------------------------

    df["service_pressure_category"] = "LOW"

    df.loc[
        df["service_pressure_score"] >= 0.50,
        "service_pressure_category"
    ] = "MEDIUM"

    df.loc[
        df["service_pressure_score"] >= 0.75,
        "service_pressure_category"
    ] = "HIGH"

    # --------------------------------------------------------
    # Select output columns
    # --------------------------------------------------------

    output_columns = [
        "trip_id",
        "route_id",
        "stop_id",
        "stop_name",
        "stop_sequence",
        "scheduled_hour",
        "trip_total_stops",
        "trip_progress_ratio",
        "is_first_stop",
        "is_last_stop",
        "is_intermediate_stop",
        "stop_lat",
        "stop_lon",
        "is_peak_hour",
        "peak_period",
        "stop_service_intensity",
        "route_stop_service_intensity",
        "stop_position_ratio",
        "scheduled_dwell_indicator",
        "route_travel_intensity",
        "hourly_route_trip_frequency",
        "hourly_stop_trip_frequency",
        "route_trip_count",
        "stop_activity_category",
        "route_service_category",
        "route_peak_service",
        "service_pressure_score",
        "service_pressure_category"
    ]

    output_df = df[
        output_columns
    ].copy()

    # --------------------------------------------------------
    # Remove duplicate rows
    # --------------------------------------------------------

    output_df = output_df.drop_duplicates()

    # --------------------------------------------------------
    # Save
    # --------------------------------------------------------

    os.makedirs(
        OUTPUT_DIR,
        exist_ok=True
    )

    output_df.to_csv(
        OUTPUT_FILE,
        index=False
    )

    # --------------------------------------------------------
    # Summary
    # --------------------------------------------------------

    print("\n" + "=" * 60)
    print("CROWD MANAGEMENT FEATURE SUMMARY")
    print("=" * 60)

    print(
        f"\nFeature observations generated: "
        f"{len(output_df)}"
    )

    print(
        f"Unique routes: "
        f"{output_df['route_id'].nunique()}"
    )

    print(
        f"Unique stops: "
        f"{output_df['stop_id'].nunique()}"
    )

    print(
        f"Unique trips: "
        f"{output_df['trip_id'].nunique()}"
    )

    print("\nPeak-period counts:")

    print(
        output_df["peak_period"]
        .value_counts()
    )

    print("\nService-pressure counts:")

    print(
        output_df["service_pressure_category"]
        .value_counts()
    )

    print("\nSample crowd-management features:")

    print(
        output_df.head(10).to_string(
            index=False
        )
    )

    print("\nSaved results to:")

    print(OUTPUT_FILE)

    print(
        "\nCrowd-management feature generation "
        "completed successfully!"
    )


if __name__ == "__main__":
    main()