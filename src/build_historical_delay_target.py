import os
import sys
import pandas as pd


# ============================================================
# CONFIGURATION
# ============================================================

TRIP_UPDATES_FILE = os.path.join(
    "data",
    "realtime",
    "vline_trip_updates_history.csv"
)

STOP_TIMES_FILE = os.path.join(
    "data",
    "static",
    "stop_times.txt"
)

TRIPS_FILE = os.path.join(
    "data",
    "static",
    "trips.txt"
)

OUTPUT_FILE = os.path.join(
    "models",
    "historical_delay_target.csv"
)


# ============================================================
# MAIN
# ============================================================

def main():

    print("=" * 60)
    print("HISTORICAL DELAY TARGET DATASET")
    print("=" * 60)

    # --------------------------------------------------------
    # Check realtime Trip Updates
    # --------------------------------------------------------

    print("\nChecking realtime Trip Updates...")

    if not os.path.exists(TRIP_UPDATES_FILE):

        print("\nREALTIME TRIP UPDATES NOT AVAILABLE")
        print("-" * 60)

        print(
            f"Expected file:\n{TRIP_UPDATES_FILE}"
        )

        print(
            "\nThe V/Line Trip Updates API is currently "
            "unreachable from this computer."
        )

        print(
            "\nTherefore, a genuine historical delay target "
            "cannot be created yet."
        )

        print("\nIMPORTANT:")
        print("  Do NOT create artificial delay values.")
        print("  Do NOT use scheduled travel time as delay.")
        print("  Do NOT train the model without genuine observations.")

        print("\nCurrent status:")
        print("  Trip Updates: NOT AVAILABLE")
        print("  delay_seconds: NOT AVAILABLE")
        print("  Model training: WAITING")

        print("\nThe script will stop safely.")

        sys.exit(0)

    # --------------------------------------------------------
    # Load Trip Updates
    # --------------------------------------------------------

    print("\nLoading realtime Trip Updates...")

    realtime = pd.read_csv(
        TRIP_UPDATES_FILE
    )

    print(
        f"Trip Update rows loaded: "
        f"{len(realtime)}"
    )

    # --------------------------------------------------------
    # Check required realtime columns
    # --------------------------------------------------------

    required_realtime_columns = [
        "trip_id",
        "stop_id",
        "stop_sequence",
        "arrival_delay_seconds",
        "departure_delay_seconds"
    ]

    missing_columns = [
        column
        for column in required_realtime_columns
        if column not in realtime.columns
    ]

    if missing_columns:

        print("\nERROR: Required realtime columns missing:")

        for column in missing_columns:
            print(f"  {column}")

        sys.exit(1)

    # --------------------------------------------------------
    # Load static GTFS stop times
    # --------------------------------------------------------

    print("\nLoading static GTFS stop times...")

    if not os.path.exists(STOP_TIMES_FILE):

        print(
            f"\nERROR: File not found:\n{STOP_TIMES_FILE}"
        )

        sys.exit(1)

    stop_times = pd.read_csv(
        STOP_TIMES_FILE
    )

    print(
        f"Static stop-time rows loaded: "
        f"{len(stop_times)}"
    )

    # --------------------------------------------------------
    # Load static GTFS trips
    # --------------------------------------------------------

    print("\nLoading static GTFS trips...")

    if not os.path.exists(TRIPS_FILE):

        print(
            f"\nERROR: File not found:\n{TRIPS_FILE}"
        )

        sys.exit(1)

    trips = pd.read_csv(
        TRIPS_FILE
    )

    print(
        f"Static trips loaded: "
        f"{len(trips)}"
    )

    # --------------------------------------------------------
    # Normalize identifiers
    # --------------------------------------------------------

    realtime["trip_id"] = (
        realtime["trip_id"]
        .astype(str)
        .str.strip()
    )

    realtime["stop_id"] = (
        realtime["stop_id"]
        .astype(str)
        .str.strip()
    )

    stop_times["trip_id"] = (
        stop_times["trip_id"]
        .astype(str)
        .str.strip()
    )

    stop_times["stop_id"] = (
        stop_times["stop_id"]
        .astype(str)
        .str.strip()
    )

    trips["trip_id"] = (
        trips["trip_id"]
        .astype(str)
        .str.strip()
    )

    # --------------------------------------------------------
    # Convert delay values
    # --------------------------------------------------------

    realtime[
        "arrival_delay_seconds"
    ] = pd.to_numeric(
        realtime["arrival_delay_seconds"],
        errors="coerce"
    )

    realtime[
        "departure_delay_seconds"
    ] = pd.to_numeric(
        realtime["departure_delay_seconds"],
        errors="coerce"
    )

    # --------------------------------------------------------
    # Choose genuine observed delay
    #
    # Prefer arrival delay when available.
    # Otherwise use departure delay.
    # --------------------------------------------------------

    realtime["delay_seconds"] = (
        realtime["arrival_delay_seconds"]
        .combine_first(
            realtime["departure_delay_seconds"]
        )
    )

    # --------------------------------------------------------
    # Remove rows without genuine delay
    # --------------------------------------------------------

    valid = realtime[
        "delay_seconds"
    ].notna()

    realtime = realtime.loc[
        valid
    ].copy()

    print(
        f"\nRows containing genuine delay values: "
        f"{len(realtime)}"
    )

    if realtime.empty:

        print("\nNO VALID DELAY OBSERVATIONS")

        print(
            "\nThe Trip Updates file exists, but it "
            "does not currently contain usable delay values."
        )

        print(
            "\nModel training will NOT start."
        )

        sys.exit(0)

    # --------------------------------------------------------
    # Convert stop sequence
    # --------------------------------------------------------

    realtime[
        "stop_sequence"
    ] = pd.to_numeric(
        realtime["stop_sequence"],
        errors="coerce"
    )

    stop_times[
        "stop_sequence"
    ] = pd.to_numeric(
        stop_times["stop_sequence"],
        errors="coerce"
    )

    # --------------------------------------------------------
    # Match realtime observations to GTFS
    # --------------------------------------------------------

    print("\nMatching realtime observations to GTFS...")

    gtfs_columns = [
        "trip_id",
        "stop_id",
        "stop_sequence",
        "arrival_time",
        "departure_time"
    ]

    gtfs = stop_times[
        gtfs_columns
    ].copy()

    merged = realtime.merge(
        gtfs,
        on=[
            "trip_id",
            "stop_id",
            "stop_sequence"
        ],
        how="inner"
    )

    print(
        f"Matched observations: "
        f"{len(merged)}"
    )

    if merged.empty:

        print(
            "\nERROR: No realtime observations "
            "could be matched to GTFS."
        )

        print(
            "\nNo training dataset will be created."
        )

        sys.exit(1)

    # --------------------------------------------------------
    # Add route/trip information
    # --------------------------------------------------------

    trip_columns = [
        "trip_id",
        "route_id",
        "service_id",
        "direction_id",
        "trip_headsign"
    ]

    trip_info = trips[
        trip_columns
    ].drop_duplicates(
        subset=["trip_id"]
    )

    merged = merged.merge(
        trip_info,
        on="trip_id",
        how="left"
    )

    # --------------------------------------------------------
    # Keep useful target fields
    # --------------------------------------------------------

    output_columns = [
        "collection_time",
        "feed_timestamp",
        "trip_timestamp",
        "trip_id",
        "route_id",
        "service_id",
        "direction_id",
        "trip_headsign",
        "stop_id",
        "stop_sequence",
        "arrival_time",
        "departure_time",
        "arrival_delay_seconds",
        "departure_delay_seconds",
        "delay_seconds"
    ]

    output_columns = [
        column
        for column in output_columns
        if column in merged.columns
    ]

    target_df = merged[
        output_columns
    ].copy()

    # --------------------------------------------------------
    # Remove duplicate observations
    # --------------------------------------------------------

    target_df = target_df.drop_duplicates()

    # --------------------------------------------------------
    # Validate target
    # --------------------------------------------------------

    target_df["delay_seconds"] = pd.to_numeric(
        target_df["delay_seconds"],
        errors="coerce"
    )

    target_df = target_df[
        target_df["delay_seconds"].notna()
    ].copy()

    print("\n" + "=" * 60)
    print("HISTORICAL DELAY TARGET SUMMARY")
    print("=" * 60)

    print(
        f"\nValid target observations: "
        f"{len(target_df)}"
    )

    print(
        f"Unique trips: "
        f"{target_df['trip_id'].nunique()}"
    )

    print(
        f"Unique stops: "
        f"{target_df['stop_id'].nunique()}"
    )

    print(
        f"Minimum delay: "
        f"{target_df['delay_seconds'].min():.2f} seconds"
    )

    print(
        f"Maximum delay: "
        f"{target_df['delay_seconds'].max():.2f} seconds"
    )

    print(
        f"Average delay: "
        f"{target_df['delay_seconds'].mean():.2f} seconds"
    )

    print(
        f"Median delay: "
        f"{target_df['delay_seconds'].median():.2f} seconds"
    )

    # --------------------------------------------------------
    # Save
    # --------------------------------------------------------

    os.makedirs(
        os.path.dirname(OUTPUT_FILE),
        exist_ok=True
    )

    target_df.to_csv(
        OUTPUT_FILE,
        index=False
    )

    print(
        "\nSaved historical delay target dataset to:"
    )

    print(
        OUTPUT_FILE
    )

    print(
        "\nHistorical delay target generation completed successfully!"
    )


# ============================================================
# RUN
# ============================================================

if __name__ == "__main__":
    main()