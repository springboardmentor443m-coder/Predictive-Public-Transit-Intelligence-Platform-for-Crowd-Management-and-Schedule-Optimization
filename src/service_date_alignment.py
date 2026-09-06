import os
import pandas as pd


# =========================================================
# SETTINGS
# =========================================================

STOP_TIMES_FILE = "data/static/stop_times.txt"

OUTPUT_FILE = "data/realtime/service_date_alignment.csv"


# =========================================================
# GTFS TIME CONVERSION
# =========================================================

def gtfs_time_to_seconds(gtfs_time):
    """
    Convert a GTFS time such as:

        23:45:00
        24:10:00
        25:23:00

    into seconds from the beginning of the GTFS service day.

    GTFS allows hours greater than 23.
    """

    if pd.isna(gtfs_time):
        return None

    value = str(gtfs_time).strip()

    parts = value.split(":")

    if len(parts) != 3:
        return None

    try:
        hours = int(parts[0])
        minutes = int(parts[1])
        seconds = int(parts[2])
    except ValueError:
        return None

    if minutes < 0 or minutes >= 60:
        return None

    if seconds < 0 or seconds >= 60:
        return None

    return (
        hours * 3600
        + minutes * 60
        + seconds
    )


# =========================================================
# CONVERT SECONDS BACK TO GTFS TIME
# =========================================================

def seconds_to_gtfs_time(total_seconds):
    """
    Convert seconds back into HH:MM:SS.

    Hours may be greater than 23.
    """

    if total_seconds is None:
        return None

    try:
        total_seconds = int(total_seconds)
    except (ValueError, TypeError):
        return None

    hours = total_seconds // 3600

    remaining = total_seconds % 3600

    minutes = remaining // 60

    seconds = remaining % 60

    return (
        f"{hours:02d}:"
        f"{minutes:02d}:"
        f"{seconds:02d}"
    )


# =========================================================
# LOAD GTFS STOP TIMES
# =========================================================

def load_stop_times():

    print(
        "Loading static GTFS stop times..."
    )

    if not os.path.exists(
        STOP_TIMES_FILE
    ):

        raise FileNotFoundError(
            f"File not found: {STOP_TIMES_FILE}"
        )

    df = pd.read_csv(
        STOP_TIMES_FILE,
        dtype={
            "trip_id": str,
            "arrival_time": str,
            "departure_time": str,
            "stop_id": str
        }
    )

    print(
        f"Stop times loaded: {len(df)}"
    )

    return df


# =========================================================
# ANALYSE GTFS TIMES
# =========================================================

def analyse_gtfs_times(df):

    print()
    print(
        "========================================"
    )
    print(
        "GTFS TIME ANALYSIS"
    )
    print(
        "========================================"
    )

    df = df.copy()

    df[
        "arrival_seconds"
    ] = df[
        "arrival_time"
    ].apply(
        gtfs_time_to_seconds
    )

    df[
        "departure_seconds"
    ] = df[
        "departure_time"
    ].apply(
        gtfs_time_to_seconds
    )

    # ---------------------------------------------
    # Identify times after midnight
    # ---------------------------------------------

    df[
        "arrival_next_day"
    ] = df[
        "arrival_seconds"
    ] >= 86400

    df[
        "departure_next_day"
    ] = df[
        "departure_seconds"
    ] >= 86400

    print(
        "Arrival times >= 24:00:00:",
        int(
            df[
                "arrival_next_day"
            ].sum()
        )
    )

    print(
        "Departure times >= 24:00:00:",
        int(
            df[
                "departure_next_day"
            ].sum()
        )
    )

    # ---------------------------------------------
    # Show maximum GTFS time
    # ---------------------------------------------

    max_arrival = df[
        "arrival_seconds"
    ].max()

    max_departure = df[
        "departure_seconds"
    ].max()

    print(
        "Maximum arrival time:",
        seconds_to_gtfs_time(
            max_arrival
        )
    )

    print(
        "Maximum departure time:",
        seconds_to_gtfs_time(
            max_departure
        )
    )

    return df


# =========================================================
# SERVICE-DAY LOGIC
# =========================================================

def add_service_day_offsets(df):

    df = df.copy()

    # -----------------------------------------------------
    # A GTFS time between 00:00:00 and 23:59:59 belongs
    # to service-day offset 0.
    #
    # A GTFS time between 24:00:00 and 47:59:59 belongs
    # to service-day offset 1.
    #
    # Example:
    #
    # 23:50:00 -> offset 0
    # 24:10:00 -> offset 1
    # 25:23:00 -> offset 1
    # -----------------------------------------------------

    df[
        "arrival_service_day_offset"
    ] = (
        df[
            "arrival_seconds"
        ] // 86400
    )

    df[
        "departure_service_day_offset"
    ] = (
        df[
            "departure_seconds"
        ] // 86400
    )

    return df


# =========================================================
# EXAMPLE V/LINE TRIP
# =========================================================

def inspect_example_trip(df):

    example_trip = (
        "01-GEL--5-T3-8819"
    )

    trip = df[
        df["trip_id"].astype(str)
        == example_trip
    ].copy()

    print()
    print(
        "========================================"
    )
    print(
        "EXAMPLE V/LINE TRIP"
    )
    print(
        "========================================"
    )

    if trip.empty:

        print(
            "Example trip not found."
        )

        return

    columns = [
        "trip_id",
        "stop_id",
        "stop_sequence",
        "arrival_time",
        "arrival_seconds",
        "arrival_service_day_offset",
        "departure_time",
        "departure_seconds",
        "departure_service_day_offset"
    ]

    available_columns = [
        column
        for column in columns
        if column in trip.columns
    ]

    print(
        trip[
            available_columns
        ].to_string(
            index=False
        )
    )


# =========================================================
# REALTIME TIMESTAMP CONVERSION
# =========================================================

def convert_realtime_timestamp(
    unix_timestamp
):
    """
    Convert a realtime Unix timestamp into
    a timezone-aware UTC datetime.
    """

    if pd.isna(
        unix_timestamp
    ):

        return pd.NaT

    try:

        return pd.to_datetime(
            int(unix_timestamp),
            unit="s",
            utc=True
        )

    except (
        ValueError,
        TypeError,
        OverflowError
    ):

        return pd.NaT


# =========================================================
# REALTIME SERVICE-DAY SECONDS
# =========================================================

def realtime_datetime_to_seconds(
    timestamp
):
    """
    Convert a realtime UTC datetime into seconds
    since midnight.

    This is only the clock-time component.

    It does NOT decide which GTFS service date applies.
    That distinction is handled separately.
    """

    if pd.isna(
        timestamp
    ):

        return None

    return (
        timestamp.hour * 3600
        + timestamp.minute * 60
        + timestamp.second
    )


# =========================================================
# BUILD ALIGNMENT EXAMPLES
# =========================================================

def build_alignment_examples():

    examples = [
        "23:30:00",
        "23:59:59",
        "24:00:00",
        "24:10:00",
        "25:23:00",
        "26:45:30"
    ]

    rows = []

    for value in examples:

        seconds = (
            gtfs_time_to_seconds(
                value
            )
        )

        service_offset = (
            seconds // 86400
            if seconds is not None
            else None
        )

        rows.append(
            {
                "gtfs_time":
                    value,

                "seconds_from_service_day_start":
                    seconds,

                "service_day_offset":
                    service_offset,

                "normalized_gtfs_time":
                    seconds_to_gtfs_time(
                        seconds
                    )
            }
        )

    return pd.DataFrame(
        rows
    )


# =========================================================
# SAVE ALIGNMENT RESULTS
# =========================================================

def save_results(df):

    os.makedirs(
        os.path.dirname(
            OUTPUT_FILE
        ),
        exist_ok=True
    )

    df.to_csv(
        OUTPUT_FILE,
        index=False
    )

    print()
    print(
        "Saved results to:"
    )

    print(
        OUTPUT_FILE
    )


# =========================================================
# MAIN
# =========================================================

def main():

    print(
        "========================================"
    )
    print(
        "GTFS SERVICE-DATE/TIME ALIGNMENT"
    )
    print(
        "========================================"
    )

    # -----------------------------------------------------
    # Load GTFS
    # -----------------------------------------------------

    df = load_stop_times()

    # -----------------------------------------------------
    # Convert times
    # -----------------------------------------------------

    df = analyse_gtfs_times(
        df
    )

    # -----------------------------------------------------
    # Add service-day offsets
    # -----------------------------------------------------

    df = add_service_day_offsets(
        df
    )

    # -----------------------------------------------------
    # Inspect the V/Line example trip
    # -----------------------------------------------------

    inspect_example_trip(
        df
    )

    # -----------------------------------------------------
    # Show explicit examples
    # -----------------------------------------------------

    print()
    print(
        "========================================"
    )
    print(
        "GTFS TIME ALIGNMENT EXAMPLES"
    )
    print(
        "========================================"
    )

    examples = build_alignment_examples()

    print(
        examples.to_string(
            index=False
        )
    )

    # -----------------------------------------------------
    # Save complete processed GTFS times
    # -----------------------------------------------------

    save_results(
        df
    )

    print()
    print(
        "GTFS service-date/time alignment "
        "completed successfully!"
    )


# =========================================================
# RUN
# =========================================================

if __name__ == "__main__":
    main()