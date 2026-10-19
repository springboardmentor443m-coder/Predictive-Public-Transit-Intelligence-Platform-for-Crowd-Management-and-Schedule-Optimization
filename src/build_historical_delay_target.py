
import os
import sys
import pandas as pd


# ============================================================
# CONFIGURATION
# ============================================================

REALTIME_FILE = os.path.join(
    "data", "realtime", "vline_trip_updates_history.csv"
)

STOP_TIMES_FILE = os.path.join(
    "data", "static", "stop_times.txt"
)

TRIPS_FILE = os.path.join(
    "data", "static", "trips.txt"
)

OUTPUT_FILE = os.path.join(
    "models", "historical_delay_target.csv"
)


# ============================================================
# HELPER FUNCTIONS
# ============================================================

def stop_program(message):
    print(f"\nERROR: {message}")
    sys.exit(1)


def load_csv(path, description, **kwargs):
    if not os.path.exists(path):
        stop_program(f"{description} not found: {path}")

    print(f"\nLoading {description}...")

    try:
        df = pd.read_csv(path, **kwargs)
    except Exception as exc:
        stop_program(f"Unable to read {path}: {exc}")

    print(f"Rows loaded: {len(df)}")
    return df


def normalize_ids(df, columns):
    for column in columns:
        if column in df.columns:
            df[column] = df[column].astype("string").str.strip()
    return df


# ============================================================
# MAIN
# ============================================================

def main():

    print("=" * 65)
    print("HISTORICAL DELAY TARGET DATASET")
    print("=" * 65)

    # --------------------------------------------------------
    # 1. Load realtime observations
    # --------------------------------------------------------

    realtime = load_csv(
        REALTIME_FILE,
        "realtime Trip Updates",
        dtype={"trip_id": "string", "stop_id": "string"}
    )

    required_realtime = [
        "trip_id",
        "stop_id",
        "stop_sequence",
        "arrival_delay_seconds",
        "departure_delay_seconds"
    ]

    missing = [
        col for col in required_realtime
        if col not in realtime.columns
    ]

    if missing:
        stop_program(
            "Realtime file is missing columns: "
            + ", ".join(missing)
        )

    # --------------------------------------------------------
    # 2. Load static GTFS schedules
    # --------------------------------------------------------

    stop_times = load_csv(
        STOP_TIMES_FILE,
        "static GTFS stop times",
        dtype={"trip_id": "string", "stop_id": "string"}
    )

    required_stop_times = [
        "trip_id",
        "stop_id",
        "stop_sequence",
        "arrival_time",
        "departure_time"
    ]

    missing = [
        col for col in required_stop_times
        if col not in stop_times.columns
    ]

    if missing:
        stop_program(
            "stop_times.txt is missing columns: "
            + ", ".join(missing)
        )

    # --------------------------------------------------------
    # 3. Load trip metadata
    # --------------------------------------------------------

    trips = load_csv(
        TRIPS_FILE,
        "static GTFS trips",
        dtype={"trip_id": "string"}
    )

    if "trip_id" not in trips.columns:
        stop_program("trips.txt does not contain trip_id.")

    # --------------------------------------------------------
    # 4. Normalize matching columns
    # --------------------------------------------------------

    realtime = normalize_ids(
        realtime, ["trip_id", "stop_id"]
    )

    stop_times = normalize_ids(
        stop_times, ["trip_id", "stop_id"]
    )

    trips = normalize_ids(trips, ["trip_id"])

    realtime["stop_sequence"] = pd.to_numeric(
        realtime["stop_sequence"], errors="coerce"
    )

    stop_times["stop_sequence"] = pd.to_numeric(
        stop_times["stop_sequence"], errors="coerce"
    )

    realtime["arrival_delay_seconds"] = pd.to_numeric(
        realtime["arrival_delay_seconds"], errors="coerce"
    )

    realtime["departure_delay_seconds"] = pd.to_numeric(
        realtime["departure_delay_seconds"], errors="coerce"
    )

    realtime = realtime.dropna(
        subset=["trip_id", "stop_id", "stop_sequence"]
    ).copy()

    stop_times = stop_times.dropna(
        subset=["trip_id", "stop_id", "stop_sequence"]
    ).copy()

    # --------------------------------------------------------
    # 5. Build target from genuine realtime delays
    # --------------------------------------------------------

    realtime["delay_seconds"] = (
        realtime["arrival_delay_seconds"].combine_first(
            realtime["departure_delay_seconds"]
        )
    )

    realtime = realtime.dropna(
        subset=["delay_seconds"]
    ).copy()

    print(
        "\nRows containing genuine delay values:",
        len(realtime)
    )

    if realtime.empty:
        stop_program("No usable realtime delay values were found.")

    # --------------------------------------------------------
    # 6. Match realtime records to scheduled stop times
    #
    # IMPORTANT:
    # Rename schedule columns before merging. This prevents
    # collisions with same-named realtime columns.
    # --------------------------------------------------------

    print("\nMatching realtime observations to GTFS...")

    gtfs = stop_times[
        [
            "trip_id",
            "stop_id",
            "stop_sequence",
            "arrival_time",
            "departure_time"
        ]
    ].copy()

    gtfs = gtfs.rename(
        columns={
            "arrival_time": "scheduled_arrival_time",
            "departure_time": "scheduled_departure_time"
        }
    )

    gtfs = gtfs.drop_duplicates(
        subset=["trip_id", "stop_id", "stop_sequence"]
    )

    merged = realtime.merge(
        gtfs,
        on=["trip_id", "stop_id", "stop_sequence"],
        how="inner",
        validate="many_to_one"
    )

    print("Matched observations:", len(merged))

    if merged.empty:
        stop_program(
            "No realtime observations matched the GTFS schedule."
        )

    # --------------------------------------------------------
    # 7. Add trip metadata without overwriting existing fields
    # --------------------------------------------------------

    metadata_candidates = [
        "route_id",
        "service_id",
        "direction_id",
        "trip_headsign",
        "shape_id"
    ]

    metadata_columns = [
        col for col in metadata_candidates
        if col in trips.columns and col not in merged.columns
    ]

    if metadata_columns:
        trip_info = trips[
            ["trip_id"] + metadata_columns
        ].drop_duplicates(subset=["trip_id"])

        merged = merged.merge(
            trip_info,
            on="trip_id",
            how="left",
            validate="many_to_one"
        )

    # --------------------------------------------------------
    # 8. Select output columns
    # --------------------------------------------------------

    preferred_columns = [
        "collection_time",
        "feed_timestamp",
        "trip_timestamp",
        "trip_id",
        "route_id",
        "service_id",
        "direction_id",
        "trip_headsign",
        "shape_id",
        "stop_id",
        "stop_sequence",
        "scheduled_arrival_time",
        "scheduled_departure_time",
        "arrival_delay_seconds",
        "departure_delay_seconds",
        "delay_seconds"
    ]

    output_columns = [
        col for col in preferred_columns
        if col in merged.columns
    ]

    target_df = merged[output_columns].copy()

    target_df["delay_seconds"] = pd.to_numeric(
        target_df["delay_seconds"], errors="coerce"
    )

    target_df = target_df.dropna(
        subset=["delay_seconds"]
    ).drop_duplicates().copy()

    # --------------------------------------------------------
    # 9. Save dataset
    # --------------------------------------------------------

    os.makedirs(os.path.dirname(OUTPUT_FILE), exist_ok=True)

    target_df.to_csv(OUTPUT_FILE, index=False)

    # --------------------------------------------------------
    # 10. Print summary
    # --------------------------------------------------------

    print("\n" + "=" * 65)
    print("HISTORICAL DELAY TARGET SUMMARY")
    print("=" * 65)

    print("Valid target observations:", len(target_df))
    print("Unique trips:", target_df["trip_id"].nunique())
    print("Unique stops:", target_df["stop_id"].nunique())

    print(
        f"Minimum delay: {target_df['delay_seconds'].min():.2f} seconds"
    )
    print(
        f"Maximum delay: {target_df['delay_seconds'].max():.2f} seconds"
    )
    print(
        f"Average delay: {target_df['delay_seconds'].mean():.2f} seconds"
    )
    print(
        f"Median delay: {target_df['delay_seconds'].median():.2f} seconds"
    )

    print("\nSaved dataset to:")
    print(OUTPUT_FILE)

    print("\nOutput columns:")
    print(target_df.columns.tolist())

    print("\nHistorical delay target generation completed successfully!")


if __name__ == "__main__":
    main()
