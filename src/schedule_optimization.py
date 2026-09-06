import os
import sys
import pandas as pd


# ============================================================
# CONFIGURATION
# ============================================================

INPUT_FILE = os.path.join(
    "data",
    "crowd",
    "crowd_management_features.csv"
)

OUTPUT_DIR = os.path.join(
    "data",
    "optimization"
)

OUTPUT_FILE = os.path.join(
    OUTPUT_DIR,
    "schedule_optimization_recommendations.csv"
)


# ============================================================
# THRESHOLDS
# ============================================================

HIGH_PRESSURE = 0.75
MEDIUM_PRESSURE = 0.50


# ============================================================
# MAIN
# ============================================================

def main():

    print("=" * 65)
    print("V/LINE SCHEDULE OPTIMIZATION")
    print("=" * 65)

    # --------------------------------------------------------
    # Load crowd-management features
    # --------------------------------------------------------

    print("\nLoading crowd-management features...")

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
        "scheduled_hour",
        "peak_period",
        "hourly_route_trip_frequency",
        "hourly_stop_trip_frequency",
        "route_trip_count",
        "service_pressure_score",
        "service_pressure_category",
        "stop_activity_category",
        "route_service_category",
        "route_peak_service",
        "route_travel_intensity",
        "scheduled_dwell_indicator",
        "trip_total_stops",
        "trip_progress_ratio"
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
        "hourly_route_trip_frequency",
        "hourly_stop_trip_frequency",
        "route_trip_count",
        "service_pressure_score",
        "route_travel_intensity",
        "scheduled_dwell_indicator",
        "trip_total_stops",
        "trip_progress_ratio"
    ]

    for column in numeric_columns:

        df[column] = pd.to_numeric(
            df[column],
            errors="coerce"
        )

    # --------------------------------------------------------
    # Create route-hour summary
    # --------------------------------------------------------

    print("\nBuilding route-hour optimization summary...")

    route_hour = (
        df.groupby(
            [
                "route_id",
                "scheduled_hour",
                "peak_period"
            ],
            dropna=False
        )
        .agg(
            trip_frequency=(
                "trip_id",
                "nunique"
            ),
            stop_count=(
                "stop_id",
                "nunique"
            ),
            average_service_pressure=(
                "service_pressure_score",
                "mean"
            ),
            maximum_service_pressure=(
                "service_pressure_score",
                "max"
            ),
            average_stop_frequency=(
                "hourly_stop_trip_frequency",
                "mean"
            ),
            average_route_frequency=(
                "hourly_route_trip_frequency",
                "mean"
            ),
            average_travel_intensity=(
                "route_travel_intensity",
                "mean"
            ),
            average_dwell=(
                "scheduled_dwell_indicator",
                "mean"
            )
        )
        .reset_index()
    )

    # --------------------------------------------------------
    # Optimization score
    # --------------------------------------------------------

    route_hour["optimization_pressure_score"] = (
        route_hour[
            "average_service_pressure"
        ]
        .rank(pct=True)
    )

    # --------------------------------------------------------
    # Recommendation classification
    # --------------------------------------------------------

    route_hour["recommendation"] = (
        "NO_CHANGE"
    )

    route_hour.loc[
        route_hour["average_service_pressure"]
        >= HIGH_PRESSURE,
        "recommendation"
    ] = "CONSIDER_ADDITIONAL_SERVICE"

    route_hour.loc[
        (
            route_hour["average_service_pressure"]
            >= MEDIUM_PRESSURE
        )
        &
        (
            route_hour["average_service_pressure"]
            < HIGH_PRESSURE
        ),
        "recommendation"
    ] = "MONITOR_SERVICE_PRESSURE"

    # --------------------------------------------------------
    # Peak-period recommendation
    # --------------------------------------------------------

    route_hour["peak_recommendation"] = (
        "NORMAL"
    )

    route_hour.loc[
        (
            route_hour["peak_period"]
            != "OFF_PEAK"
        )
        &
        (
            route_hour["average_service_pressure"]
            >= HIGH_PRESSURE
        ),
        "peak_recommendation"
    ] = "HIGH_PEAK_PRESSURE"

    route_hour.loc[
        (
            route_hour["peak_period"]
            != "OFF_PEAK"
        )
        &
        (
            route_hour["average_service_pressure"]
            >= MEDIUM_PRESSURE
        )
        &
        (
            route_hour["average_service_pressure"]
            < HIGH_PRESSURE
        ),
        "peak_recommendation"
    ] = "MODERATE_PEAK_PRESSURE"

    # --------------------------------------------------------
    # Service frequency recommendation
    # --------------------------------------------------------

    route_hour["frequency_recommendation"] = (
        "MAINTAIN_CURRENT_FREQUENCY"
    )

    route_hour.loc[
        route_hour["average_service_pressure"]
        >= HIGH_PRESSURE,
        "frequency_recommendation"
    ] = "EVALUATE_FREQUENCY_INCREASE"

    # --------------------------------------------------------
    # Stop-level pressure summary
    # --------------------------------------------------------

    stop_summary = (
        df.groupby(
            [
                "route_id",
                "stop_id",
                "stop_name"
            ],
            dropna=False
        )
        .agg(
            stop_trip_frequency=(
                "trip_id",
                "nunique"
            ),
            average_service_pressure=(
                "service_pressure_score",
                "mean"
            ),
            maximum_service_pressure=(
                "service_pressure_score",
                "max"
            ),
            peak_observations=(
                "is_peak_hour",
                "sum"
            )
        )
        .reset_index()
    )

    stop_summary["stop_recommendation"] = (
        "NORMAL_STOP_ACTIVITY"
    )

    stop_summary.loc[
        stop_summary["average_service_pressure"]
        >= HIGH_PRESSURE,
        "stop_recommendation"
    ] = "PRIORITY_STOP_FOR_MONITORING"

    stop_summary.loc[
        (
            stop_summary["average_service_pressure"]
            >= MEDIUM_PRESSURE
        )
        &
        (
            stop_summary["average_service_pressure"]
            < HIGH_PRESSURE
        ),
        "stop_recommendation"
    ] = "MONITOR_STOP_ACTIVITY"

    # --------------------------------------------------------
    # Merge stop information into route-hour dataset
    # --------------------------------------------------------

    route_hour["priority_stop_count"] = 0

    priority_counts = (
        stop_summary[
            stop_summary["stop_recommendation"]
            == "PRIORITY_STOP_FOR_MONITORING"
        ]
        .groupby("route_id")
        .size()
        .rename("priority_stop_count")
        .reset_index()
    )

    route_hour = route_hour.drop(
        columns=["priority_stop_count"],
        errors="ignore"
    )

    route_hour = route_hour.merge(
        priority_counts,
        on="route_id",
        how="left"
    )

    route_hour["priority_stop_count"] = (
        route_hour["priority_stop_count"]
        .fillna(0)
        .astype(int)
    )

    # --------------------------------------------------------
    # Overall action
    # --------------------------------------------------------

    route_hour["recommended_action"] = (
        "CONTINUE_MONITORING"
    )

    route_hour.loc[
        route_hour["recommendation"]
        == "CONSIDER_ADDITIONAL_SERVICE",
        "recommended_action"
    ] = "EVALUATE_ADDITIONAL_SERVICE"

    route_hour.loc[
        (
            route_hour["recommendation"]
            == "MONITOR_SERVICE_PRESSURE"
        )
        &
        (
            route_hour["peak_period"]
            != "OFF_PEAK"
        ),
        "recommended_action"
    ] = "MONITOR_PEAK_PERIOD"

    # --------------------------------------------------------
    # Save route-hour recommendations
    # --------------------------------------------------------

    os.makedirs(
        OUTPUT_DIR,
        exist_ok=True
    )

    route_hour.to_csv(
        OUTPUT_FILE,
        index=False
    )

    # --------------------------------------------------------
    # Save stop recommendations separately
    # --------------------------------------------------------

    stop_output = os.path.join(
        OUTPUT_DIR,
        "stop_optimization_recommendations.csv"
    )

    stop_summary.to_csv(
        stop_output,
        index=False
    )

    # --------------------------------------------------------
    # Summary
    # --------------------------------------------------------

    print("\n" + "=" * 65)
    print("SCHEDULE OPTIMIZATION SUMMARY")
    print("=" * 65)

    print(
        f"\nRoute-hour observations: "
        f"{len(route_hour)}"
    )

    print(
        f"Routes analysed: "
        f"{route_hour['route_id'].nunique()}"
    )

    print(
        f"Stops analysed: "
        f"{stop_summary['stop_id'].nunique()}"
    )

    print("\nRecommendation counts:")

    print(
        route_hour["recommendation"]
        .value_counts()
    )

    print("\nPeak recommendations:")

    print(
        route_hour["peak_recommendation"]
        .value_counts()
    )

    print("\nTop pressure periods:")

    top_pressure = (
        route_hour
        .sort_values(
            "average_service_pressure",
            ascending=False
        )
        .head(10)
    )

    print(
        top_pressure[
            [
                "route_id",
                "scheduled_hour",
                "peak_period",
                "trip_frequency",
                "average_service_pressure",
                "recommendation",
                "recommended_action"
            ]
        ].to_string(index=False)
    )

    print("\nSaved route-hour recommendations to:")
    print(OUTPUT_FILE)

    print("\nSaved stop recommendations to:")
    print(stop_output)

    print(
        "\nSchedule optimization generation "
        "completed successfully!"
    )

    print(
        "\nIMPORTANT:"
        "\nThese are data-driven recommendations."
        "\nThey do not represent actual timetable changes."
    )


if __name__ == "__main__":
    main()