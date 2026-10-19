import os
from datetime import datetime, timezone

import pandas as pd


# =========================================================
# SETTINGS
# =========================================================

INPUT_FILE = "data/realtime/vline_vehicle_history.csv"

OUTPUT_FILE = "data/realtime/robust_delay_analysis.csv"

MAX_VEHICLE_TIMESTAMP_AGE_SECONDS = 300

MIN_POSITION_CHANGE_KM = 0.01

MIN_DELAY_MINUTES = -10

MAX_DELAY_MINUTES = 180


# =========================================================
# TIME HELPERS
# =========================================================

def parse_collection_time(value):
    try:
        timestamp = pd.to_datetime(
            value,
            utc=True
        )

        return timestamp

    except Exception:
        return pd.NaT


def get_current_utc_time():
    return datetime.now(
        timezone.utc
    )


# =========================================================
# LOAD REALTIME DATA
# =========================================================

def load_realtime_data():

    print(
        "Loading realtime vehicle history..."
    )

    if not os.path.exists(
        INPUT_FILE
    ):

        raise FileNotFoundError(
            f"Input file not found: {INPUT_FILE}"
        )

    df = pd.read_csv(
        INPUT_FILE
    )

    if df.empty:

        raise ValueError(
            "Realtime vehicle history is empty."
        )

    print(
        f"Realtime observations loaded: {len(df)}"
    )

    return df


# =========================================================
# CLEAN DATA
# =========================================================

def clean_data(df):

    required_columns = [
        "collection_time",
        "vehicle_id",
        "trip_id",
        "latitude",
        "longitude",
        "vehicle_timestamp",
        "feed_timestamp"
    ]

    missing = [
        column
        for column in required_columns
        if column not in df.columns
    ]

    if missing:

        raise ValueError(
            "Missing required columns: "
            + ", ".join(missing)
        )

    df = df.copy()

    df[
        "collection_time"
    ] = df[
        "collection_time"
    ].apply(
        parse_collection_time
    )

    df[
        "vehicle_timestamp"
    ] = pd.to_numeric(
        df[
            "vehicle_timestamp"
        ],
        errors="coerce"
    )

    df[
        "feed_timestamp"
    ] = pd.to_numeric(
        df[
            "feed_timestamp"
        ],
        errors="coerce"
    )

    df[
        "latitude"
    ] = pd.to_numeric(
        df[
            "latitude"
        ],
        errors="coerce"
    )

    df[
        "longitude"
    ] = pd.to_numeric(
        df[
            "longitude"
        ],
        errors="coerce"
    )

    df = df.sort_values(
        [
            "vehicle_id",
            "collection_time"
        ]
    ).reset_index(
        drop=True
    )

    return df


# =========================================================
# POSITION DISTANCE
# =========================================================

def haversine_distance(
    lat1,
    lon1,
    lat2,
    lon2
):

    from math import (
        radians,
        sin,
        cos,
        sqrt,
        atan2
    )

    if any(
        pd.isna(value)
        for value in [
            lat1,
            lon1,
            lat2,
            lon2
        ]
    ):

        return None

    earth_radius_km = 6371.0

    lat1 = radians(lat1)
    lat2 = radians(lat2)

    delta_lat = radians(
        lat2 - lat1
    )

    delta_lon = radians(
        lon2 - radians(lon1)
        if False
        else lon2 - lon1
    )

    a = (
        sin(delta_lat / 2) ** 2
        +
        cos(lat1)
        * cos(lat2)
        * sin(delta_lon / 2) ** 2
    )

    c = 2 * atan2(
        sqrt(a),
        sqrt(1 - a)
    )

    return earth_radius_km * c


# =========================================================
# REALTIME QUALITY CHECK
# =========================================================

def calculate_quality(df):

    print()
    print(
        "========================================"
    )
    print(
        "REALTIME QUALITY CHECK"
    )
    print(
        "========================================"
    )

    now = get_current_utc_time()

    ages = []

    quality_statuses = []

    previous_vehicle_timestamp = {}

    previous_latitude = {}

    previous_longitude = {}

    position_changes = []

    timestamp_changes = []

    for index, row in df.iterrows():

        vehicle_id = row[
            "vehicle_id"
        ]

        collection_time = row[
            "collection_time"
        ]

        vehicle_timestamp = row[
            "vehicle_timestamp"
        ]

        # ---------------------------------------------
        # Timestamp age
        # ---------------------------------------------

        if pd.isna(
            vehicle_timestamp
        ):

            age_seconds = None

        else:

            vehicle_time = pd.to_datetime(
                vehicle_timestamp,
                unit="s",
                utc=True
            )

            age_seconds = (
                collection_time
                - vehicle_time
            ).total_seconds()

        ages.append(
            age_seconds
        )

        # ---------------------------------------------
        # Timestamp changed?
        # ---------------------------------------------

        previous_timestamp = (
            previous_vehicle_timestamp.get(
                vehicle_id
            )
        )

        timestamp_changed = (
            previous_timestamp is None
            or vehicle_timestamp
            != previous_timestamp
        )

        timestamp_changes.append(
            timestamp_changed
        )

        previous_vehicle_timestamp[
            vehicle_id
        ] = vehicle_timestamp

        # ---------------------------------------------
        # Position changed?
        # ---------------------------------------------

        previous_lat = (
            previous_latitude.get(
                vehicle_id
            )
        )

        previous_lon = (
            previous_longitude.get(
                vehicle_id
            )
        )

        if (
            previous_lat is None
            or previous_lon is None
        ):

            position_changed = False

        else:

            distance = haversine_distance(
                previous_lat,
                previous_lon,
                row["latitude"],
                row["longitude"]
            )

            position_changed = (
                distance is not None
                and distance
                >= MIN_POSITION_CHANGE_KM
            )

        position_changes.append(
            position_changed
        )

        previous_latitude[
            vehicle_id
        ] = row["latitude"]

        previous_longitude[
            vehicle_id
        ] = row["longitude"]

        # ---------------------------------------------
        # Quality classification
        # ---------------------------------------------

        if pd.isna(
            vehicle_timestamp
        ):

            status = "MISSING_TIMESTAMP"

        elif age_seconds > (
            MAX_VEHICLE_TIMESTAMP_AGE_SECONDS
        ):

            status = "STALE"

        elif not timestamp_changed:

            status = "REPEATED_TIMESTAMP"

        else:

            status = "VALID"

        quality_statuses.append(
            status
        )

    df[
        "vehicle_timestamp_age_seconds"
    ] = ages

    df[
        "vehicle_timestamp_changed"
    ] = timestamp_changes

    df[
        "position_changed"
    ] = position_changes

    df[
        "quality_status"
    ] = quality_statuses

    return df


# =========================================================
# MOVEMENT ANALYSIS
# =========================================================

def calculate_movement(df):

    print()
    print(
        "========================================"
    )
    print(
        "MOVEMENT ANALYSIS"
    )
    print(
        "========================================"
    )

    distances = []
    elapsed_minutes = []
    speeds = []
    movement_statuses = []

    previous_rows = {}

    for index, row in df.iterrows():

        vehicle_id = row[
            "vehicle_id"
        ]

        previous = previous_rows.get(
            vehicle_id
        )

        if previous is None:

            distances.append(0.0)

            elapsed_minutes.append(
                0.0
            )

            speeds.append(
                None
            )

            movement_statuses.append(
                "FIRST_OBSERVATION"
            )

        else:

            distance = haversine_distance(
                previous["latitude"],
                previous["longitude"],
                row["latitude"],
                row["longitude"]
            )

            if distance is None:
                distance = 0.0

            elapsed = (
                row["collection_time"]
                - previous["collection_time"]
            ).total_seconds() / 60

            if elapsed <= 0:

                speed = None

            else:

                speed = (
                    distance
                    / elapsed
                    * 60
                )

            distances.append(
                distance
            )

            elapsed_minutes.append(
                elapsed
            )

            speeds.append(
                speed
            )

            if (
                row["quality_status"]
                in [
                    "STALE",
                    "REPEATED_TIMESTAMP",
                    "MISSING_TIMESTAMP"
                ]
            ):

                movement_statuses.append(
                    "UNUSABLE_REALTIME"
                )

            elif distance < MIN_POSITION_CHANGE_KM:

                movement_statuses.append(
                    "NO_MOVEMENT"
                )

            else:

                movement_statuses.append(
                    "MOVING"
                )

        previous_rows[
            vehicle_id
        ] = row

    df[
        "distance_from_previous_km"
    ] = distances

    df[
        "elapsed_from_previous_min"
    ] = elapsed_minutes

    df[
        "estimated_speed_kmh"
    ] = speeds

    df[
        "movement_status"
    ] = movement_statuses

    return df


# =========================================================
# DELAY LOGIC
# =========================================================

def calculate_delay(df):

    print()
    print(
        "========================================"
    )
    print(
        "DELAY ELIGIBILITY"
    )
    print(
        "========================================"
    )

    delay_minutes = []

    delay_statuses = []

    for index, row in df.iterrows():

        quality = row[
            "quality_status"
        ]

        movement = row[
            "movement_status"
        ]

        # ---------------------------------------------
        # Never calculate delay from stale data
        # ---------------------------------------------

        if quality != "VALID":

            delay_minutes.append(
                None
            )

            delay_statuses.append(
                "REALTIME_DATA_NOT_VALID"
            )

            continue

        # ---------------------------------------------
        # We need a valid vehicle timestamp
        # ---------------------------------------------

        vehicle_timestamp = row[
            "vehicle_timestamp"
        ]

        if pd.isna(
            vehicle_timestamp
        ):

            delay_minutes.append(
                None
            )

            delay_statuses.append(
                "MISSING_VEHICLE_TIMESTAMP"
            )

            continue

        # ---------------------------------------------
        # Convert vehicle timestamp to UTC
        # ---------------------------------------------

        observed_time = pd.to_datetime(
            vehicle_timestamp,
            unit="s",
            utc=True
        )

        # ---------------------------------------------
        # We intentionally do NOT compare the raw
        # UTC timestamp against GTFS service times here.
        #
        # GTFS V/Line times can exceed 24:00:00 and
        # require service-date handling.
        #
        # Until service-date alignment is available,
        # delay is marked as PENDING rather than
        # producing misleading numbers.
        # ---------------------------------------------

        delay_minutes.append(
            None
        )

        if movement == "MOVING":

            delay_statuses.append(
                "READY_FOR_SERVICE_DATE_ALIGNMENT"
            )

        else:

            delay_statuses.append(
                "VALID_REALTIME_DELAY_PENDING"
            )

    df[
        "delay_minutes"
    ] = delay_minutes

    df[
        "delay_status"
    ] = delay_statuses

    return df


# =========================================================
# SUMMARY
# =========================================================

def print_summary(df):

    print()
    print(
        "========================================"
    )
    print(
        "ROBUST REALTIME DELAY SUMMARY"
    )
    print(
        "========================================"
    )

    print(
        f"Observations analysed: {len(df)}"
    )

    print()

    print(
        "Quality status counts:"
    )

    print(
        df[
            "quality_status"
        ].value_counts()
    )

    print()

    print(
        "Movement status counts:"
    )

    print(
        df[
            "movement_status"
        ].value_counts()
    )

    print()

    print(
        "Delay status counts:"
    )

    print(
        df[
            "delay_status"
        ].value_counts()
    )

    print()

    valid = df[
        df["quality_status"]
        == "VALID"
    ]

    print(
        f"Valid realtime observations: "
        f"{len(valid)}"
    )

    if len(valid) > 0:

        print(
            "Fresh realtime data is available."
        )

    else:

        print(
            "No fresh realtime observations "
            "are currently available."
        )


# =========================================================
# SAVE RESULTS
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
        "ROBUST REALTIME DELAY ANALYSIS"
    )

    print(
        "========================================"
    )

    df = load_realtime_data()

    df = clean_data(
        df
    )

    df = calculate_quality(
        df
    )

    df = calculate_movement(
        df
    )

    df = calculate_delay(
        df
    )

    print_summary(
        df
    )

    save_results(
        df
    )

    print()
    print(
        "Robust realtime delay analysis "
        "completed successfully!"
    )


# =========================================================
# RUN
# =========================================================

if __name__ == "__main__":
    main()