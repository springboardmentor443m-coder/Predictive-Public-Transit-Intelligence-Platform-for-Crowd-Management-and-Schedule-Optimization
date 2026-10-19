import os
import math
import pandas as pd


# =========================================================
# FILE PATHS
# =========================================================

REALTIME_FILE = "data/realtime/vline_vehicle_history.csv"

QUALITY_FILE = "data/realtime/realtime_data_quality.csv"

MOVEMENT_FILE = "data/realtime/vline_movement_analysis.csv"

STOP_TIMES_FILE = "data/static/stop_times.txt"

STOPS_FILE = "data/static/stops.txt"

OUTPUT_FILE = "data/realtime/validated_delay_features.csv"


# =========================================================
# SETTINGS
# =========================================================

# Maximum distance at which a vehicle observation can be
# associated with a scheduled stop.
MAX_STOP_DISTANCE_KM = 2.0

# A realtime vehicle timestamp older than this is considered
# unusable.
MAX_TIMESTAMP_AGE_SECONDS = 180.0

# Minimum movement distance considered meaningful.
MIN_MOVEMENT_KM = 0.01


# =========================================================
# GTFS TIME CONVERSION
# =========================================================

def gtfs_time_to_seconds(value):

    if pd.isna(value):
        return None

    value = str(value).strip()

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
# LOAD REALTIME DATA
# =========================================================

def load_realtime():

    print()
    print("Loading realtime vehicle history...")

    if not os.path.exists(REALTIME_FILE):
        raise FileNotFoundError(
            f"Realtime file not found: {REALTIME_FILE}"
        )

    df = pd.read_csv(
        REALTIME_FILE,
        dtype={
            "vehicle_id": str,
            "trip_id": str,
            "route_id": str
        }
    )

    if df.empty:
        raise ValueError(
            "Realtime vehicle history is empty."
        )

    df["collection_time"] = pd.to_datetime(
        df["collection_time"],
        utc=True,
        errors="coerce"
    )

    print(
        f"Realtime observations loaded: {len(df)}"
    )

    return df


# =========================================================
# LOAD QUALITY DATA
# =========================================================

def load_quality():

    print(
        "Loading realtime data quality results..."
    )

    if not os.path.exists(QUALITY_FILE):

        print(
            "Quality file not found."
        )

        return pd.DataFrame()

    df = pd.read_csv(
        QUALITY_FILE,
        dtype={
            "vehicle_id": str,
            "trip_id": str
        }
    )

    if "collection_time" in df.columns:

        df["collection_time"] = pd.to_datetime(
            df["collection_time"],
            utc=True,
            errors="coerce"
        )

    print(
        f"Quality observations loaded: {len(df)}"
    )

    return df


# =========================================================
# LOAD MOVEMENT DATA
# =========================================================

def load_movement():

    print(
        "Loading realtime movement analysis..."
    )

    if not os.path.exists(MOVEMENT_FILE):

        print(
            "Movement file not found."
        )

        return pd.DataFrame()

    df = pd.read_csv(
        MOVEMENT_FILE,
        dtype={
            "vehicle_id": str,
            "trip_id": str
        }
    )

    if "collection_time" in df.columns:

        df["collection_time"] = pd.to_datetime(
            df["collection_time"],
            utc=True,
            errors="coerce"
        )

    print(
        f"Movement observations loaded: {len(df)}"
    )

    return df


# =========================================================
# LOAD GTFS STOPS
# =========================================================

def load_stops():

    print(
        "Loading static GTFS stops..."
    )

    if not os.path.exists(STOPS_FILE):

        raise FileNotFoundError(
            f"Stops file not found: {STOPS_FILE}"
        )

    df = pd.read_csv(
        STOPS_FILE,
        dtype={
            "stop_id": str
        }
    )

    print(
        f"Static stops loaded: {len(df)}"
    )

    return df


# =========================================================
# LOAD GTFS STOP TIMES
# =========================================================

def load_stop_times():

    print(
        "Loading static GTFS stop times..."
    )

    if not os.path.exists(STOP_TIMES_FILE):

        raise FileNotFoundError(
            f"Stop times file not found: {STOP_TIMES_FILE}"
        )

    df = pd.read_csv(
        STOP_TIMES_FILE,
        dtype={
            "trip_id": str,
            "stop_id": str,
            "arrival_time": str,
            "departure_time": str
        }
    )

    print(
        f"Static stop times loaded: {len(df)}"
    )

    return df


# =========================================================
# HAVERSINE DISTANCE
# =========================================================

def haversine_km(
    lat1,
    lon1,
    lat2,
    lon2
):

    if any(
        pd.isna(value)
        for value in [
            lat1,
            lon1,
            lat2,
            lon2
        ]
    ):
        return math.inf

    radius = 6371.0

    lat1 = math.radians(float(lat1))
    lon1 = math.radians(float(lon1))

    lat2 = math.radians(float(lat2))
    lon2 = math.radians(float(lon2))

    dlat = lat2 - lat1
    dlon = lon2 - lon1

    a = (
        math.sin(dlat / 2) ** 2
        +
        math.cos(lat1)
        *
        math.cos(lat2)
        *
        math.sin(dlon / 2) ** 2
    )

    c = 2 * math.atan2(
        math.sqrt(a),
        math.sqrt(1 - a)
    )

    return radius * c


# =========================================================
# PREPARE GTFS STOP TIMES
# =========================================================

def prepare_gtfs(
    stop_times,
    stops
):

    stop_times = stop_times.copy()

    stops = stops.copy()

    # ---------------------------------------------
    # Convert GTFS extended times
    # ---------------------------------------------

    stop_times[
        "arrival_seconds"
    ] = stop_times[
        "arrival_time"
    ].apply(
        gtfs_time_to_seconds
    )

    stop_times[
        "departure_seconds"
    ] = stop_times[
        "departure_time"
    ].apply(
        gtfs_time_to_seconds
    )

    stop_times[
        "service_day_offset"
    ] = (
        stop_times[
            "arrival_seconds"
        ] // 86400
    )

    # ---------------------------------------------
    # Merge stop coordinates
    # ---------------------------------------------

    stop_coordinates = stops[
        [
            "stop_id",
            "stop_lat",
            "stop_lon"
        ]
    ].copy()

    stop_times = stop_times.merge(
        stop_coordinates,
        on="stop_id",
        how="left"
    )

    return stop_times


# =========================================================
# MATCH NEAREST SCHEDULED STOP
# =========================================================

def find_nearest_stop(
    latitude,
    longitude,
    trip_stop_times
):

    if trip_stop_times.empty:
        return None

    best_index = None
    best_distance = math.inf

    for index, row in trip_stop_times.iterrows():

        distance = haversine_km(
            latitude,
            longitude,
            row["stop_lat"],
            row["stop_lon"]
        )

        if distance < best_distance:

            best_distance = distance
            best_index = index

    if best_index is None:
        return None

    if best_distance > MAX_STOP_DISTANCE_KM:
        return None

    result = (
        trip_stop_times
        .loc[best_index]
        .copy()
    )

    result[
        "distance_to_stop_km"
    ] = best_distance

    return result


# =========================================================
# REALTIME TIMESTAMP AGE
# =========================================================

def calculate_timestamp_age(
    collection_time,
    vehicle_timestamp
):

    if pd.isna(collection_time):
        return None

    if pd.isna(vehicle_timestamp):
        return None

    try:

        vehicle_datetime = pd.to_datetime(
            float(vehicle_timestamp),
            unit="s",
            utc=True
        )

        age = (
            collection_time
            - vehicle_datetime
        ).total_seconds()

        return age

    except (
        ValueError,
        TypeError,
        OverflowError
    ):

        return None


# =========================================================
# DETERMINE REALTIME QUALITY
# =========================================================

def determine_quality(
    timestamp_age,
    quality_status=None,
    prediction_usability=None
):

    if (
        prediction_usability
        == "NOT_USABLE"
    ):
        return "NOT_USABLE"

    if (
        quality_status
        == "STALE_VEHICLE_TIMESTAMP"
    ):
        return "STALE"

    if (
        quality_status
        == "STALE"
    ):
        return "STALE"

    if timestamp_age is None:
        return "UNKNOWN"

    if timestamp_age < 0:
        return "INVALID_FUTURE_TIMESTAMP"

    if (
        timestamp_age
        > MAX_TIMESTAMP_AGE_SECONDS
    ):
        return "STALE"

    return "FRESH"


# =========================================================
# DETERMINE MOVEMENT
# =========================================================

def determine_movement(
    row
):

    movement_status = row.get(
        "movement_status",
        None
    )

    if pd.notna(movement_status):

        if movement_status in [
            "MOVING",
            "MOVEMENT_DETECTED"
        ]:
            return "MOVING"

        if movement_status == "NO_MOVEMENT":
            return "NO_MOVEMENT"

        if movement_status == "FIRST_OBSERVATION":
            return "FIRST_OBSERVATION"

        if movement_status == "UNUSABLE_REALTIME":
            return "UNUSABLE"

    distance = row.get(
        "distance_from_previous_km",
        None
    )

    if pd.notna(distance):

        try:

            if float(distance) >= MIN_MOVEMENT_KM:
                return "MOVING"

            return "NO_MOVEMENT"

        except (
            ValueError,
            TypeError
        ):
            pass

    return "UNKNOWN"


# =========================================================
# DETERMINE DELAY ELIGIBILITY
# =========================================================

def determine_delay_eligibility(
    realtime_quality,
    movement_status,
    nearest_stop_found,
    scheduled_time_found
):

    if realtime_quality != "FRESH":
        return "NOT_ELIGIBLE"

    if not nearest_stop_found:
        return "NOT_ELIGIBLE"

    if not scheduled_time_found:
        return "NOT_ELIGIBLE"

    if movement_status == "UNUSABLE":
        return "NOT_ELIGIBLE"

    return "ELIGIBLE"


# =========================================================
# CALCULATE DELAY
# =========================================================

def calculate_delay(
    realtime_seconds,
    scheduled_seconds
):

    if (
        realtime_seconds is None
        or scheduled_seconds is None
    ):
        return None

    delay_seconds = (
        realtime_seconds
        - scheduled_seconds
    )

    return round(
        delay_seconds / 60.0,
        2
    )


# =========================================================
# PROCESS OBSERVATIONS
# =========================================================

def process_observations(
    realtime,
    quality,
    movement,
    stop_times
):

    print()
    print(
        "========================================"
    )
    print(
        "VALIDATED DELAY FEATURE GENERATION"
    )
    print(
        "========================================"
    )

    results = []

    # ---------------------------------------------
    # Index supporting datasets
    # ---------------------------------------------

    quality_lookup = {}

    if not quality.empty:

        for _, row in quality.iterrows():

            key = (
                str(row.get("vehicle_id", "")),
                str(row.get("trip_id", "")),
                str(row.get("collection_time", ""))
            )

            quality_lookup[key] = row

    movement_lookup = {}

    if not movement.empty:

        for _, row in movement.iterrows():

            key = (
                str(row.get("vehicle_id", "")),
                str(row.get("trip_id", "")),
                str(row.get("collection_time", ""))
            )

            movement_lookup[key] = row

    # ---------------------------------------------
    # Process each realtime observation
    # ---------------------------------------------

    for _, observation in realtime.iterrows():

        vehicle_id = str(
            observation.get(
                "vehicle_id",
                ""
            )
        )

        trip_id = str(
            observation.get(
                "trip_id",
                ""
            )
        )

        collection_time = observation.get(
            "collection_time",
            pd.NaT
        )

        latitude = observation.get(
            "latitude",
            None
        )

        longitude = observation.get(
            "longitude",
            None
        )

        vehicle_timestamp = observation.get(
            "vehicle_timestamp",
            None
        )

        feed_timestamp = observation.get(
            "feed_timestamp",
            None
        )

        # -----------------------------------------
        # Supporting quality record
        # -----------------------------------------

        key = (
            vehicle_id,
            trip_id,
            str(collection_time)
        )

        quality_row = quality_lookup.get(
            key
        )

        movement_row = movement_lookup.get(
            key
        )

        quality_status = None

        prediction_usability = None

        if quality_row is not None:

            quality_status = quality_row.get(
                "quality_status",
                None
            )

            prediction_usability = (
                quality_row.get(
                    "prediction_usability",
                    None
                )
            )

        # -----------------------------------------
        # Timestamp age
        # -----------------------------------------

        timestamp_age = (
            calculate_timestamp_age(
                collection_time,
                vehicle_timestamp
            )
        )

        realtime_quality = determine_quality(
            timestamp_age,
            quality_status,
            prediction_usability
        )

        # -----------------------------------------
        # Movement
        # -----------------------------------------

        movement_status = "UNKNOWN"

        if movement_row is not None:

            movement_status = (
                determine_movement(
                    movement_row
                )
            )

        # -----------------------------------------
        # Scheduled stops for trip
        # -----------------------------------------

        trip_stops = stop_times[
            stop_times["trip_id"].astype(str)
            == trip_id
        ].copy()

        nearest = find_nearest_stop(
            latitude,
            longitude,
            trip_stops
        )

        # -----------------------------------------
        # Default values
        # -----------------------------------------

        nearest_stop_id = None
        nearest_stop_name = None
        distance_to_stop_km = None

        scheduled_arrival = None
        scheduled_departure = None

        scheduled_seconds = None
        service_day_offset = None
        stop_sequence = None

        nearest_stop_found = False
        scheduled_time_found = False

        # -----------------------------------------
        # Scheduled stop match
        # -----------------------------------------

        if nearest is not None:

            nearest_stop_found = True

            nearest_stop_id = nearest.get(
                "stop_id",
                None
            )

            nearest_stop_name = nearest.get(
                "stop_name",
                None
            )

            if pd.isna(nearest_stop_name):

                nearest_stop_name = None

            distance_to_stop_km = nearest.get(
                "distance_to_stop_km",
                None
            )

            scheduled_arrival = nearest.get(
                "arrival_time",
                None
            )

            scheduled_departure = nearest.get(
                "departure_time",
                None
            )

            scheduled_seconds = nearest.get(
                "arrival_seconds",
                None
            )

            service_day_offset = nearest.get(
                "service_day_offset",
                None
            )

            stop_sequence = nearest.get(
                "stop_sequence",
                None
            )

            if (
                pd.notna(scheduled_seconds)
            ):
                scheduled_time_found = True

        # -----------------------------------------
        # Realtime clock seconds
        # -----------------------------------------

        realtime_datetime = (
            pd.NaT
        )

        realtime_seconds = None

        if pd.notna(
            vehicle_timestamp
        ):

            try:

                realtime_datetime = pd.to_datetime(
                    float(vehicle_timestamp),
                    unit="s",
                    utc=True
                )

                realtime_seconds = (
                    realtime_datetime.hour * 3600
                    + realtime_datetime.minute * 60
                    + realtime_datetime.second
                )

            except (
                ValueError,
                TypeError,
                OverflowError
            ):
                realtime_seconds = None

        # -----------------------------------------
        # Delay eligibility
        # -----------------------------------------

        delay_eligibility = (
            determine_delay_eligibility(
                realtime_quality,
                movement_status,
                nearest_stop_found,
                scheduled_time_found
            )
        )

        # -----------------------------------------
        # Delay
        # -----------------------------------------

        delay_minutes = None

        if delay_eligibility == "ELIGIBLE":

            delay_minutes = calculate_delay(
                realtime_seconds,
                scheduled_seconds
            )

        # -----------------------------------------
        # Delay status
        # -----------------------------------------

        if delay_eligibility != "ELIGIBLE":

            delay_status = (
                "REALTIME_DATA_NOT_VALID"
            )

        elif delay_minutes is None:

            delay_status = (
                "DELAY_NOT_AVAILABLE"
            )

        elif delay_minutes < -2:

            delay_status = "EARLY"

        elif delay_minutes <= 2:

            delay_status = "ON_TIME"

        elif delay_minutes <= 10:

            delay_status = "DELAYED"

        else:

            delay_status = "SEVERELY_DELAYED"

        # -----------------------------------------
        # Feature row
        # -----------------------------------------

        results.append(
            {
                "collection_time":
                    collection_time,

                "vehicle_id":
                    vehicle_id,

                "trip_id":
                    trip_id,

                "latitude":
                    latitude,

                "longitude":
                    longitude,

                "vehicle_timestamp":
                    vehicle_timestamp,

                "feed_timestamp":
                    feed_timestamp,

                "realtime_timestamp":
                    realtime_datetime,

                "vehicle_timestamp_age_seconds":
                    timestamp_age,

                "realtime_quality":
                    realtime_quality,

                "movement_status":
                    movement_status,

                "nearest_stop_id":
                    nearest_stop_id,

                "nearest_stop_name":
                    nearest_stop_name,

                "distance_to_stop_km":
                    distance_to_stop_km,

                "scheduled_arrival":
                    scheduled_arrival,

                "scheduled_departure":
                    scheduled_departure,

                "scheduled_time_seconds":
                    scheduled_seconds,

                "service_day_offset":
                    service_day_offset,

                "stop_sequence":
                    stop_sequence,

                "realtime_time_seconds":
                    realtime_seconds,

                "delay_eligibility":
                    delay_eligibility,

                "delay_minutes":
                    delay_minutes,

                "delay_status":
                    delay_status
            }
        )

    return pd.DataFrame(
        results
    )


# =========================================================
# SUMMARY
# =========================================================

def print_summary(
    results
):

    print()
    print(
        "========================================"
    )
    print(
        "VALIDATED DELAY FEATURE SUMMARY"
    )
    print(
        "========================================"
    )

    print(
        "Observations analysed:",
        len(results)
    )

    if results.empty:
        print(
            "No observations available."
        )
        return

    print()
    print(
        "Realtime quality counts:"
    )

    print(
        results[
            "realtime_quality"
        ].value_counts(
            dropna=False
        ).to_string()
    )

    print()
    print(
        "Movement status counts:"
    )

    print(
        results[
            "movement_status"
        ].value_counts(
            dropna=False
        ).to_string()
    )

    print()
    print(
        "Delay eligibility counts:"
    )

    print(
        results[
            "delay_eligibility"
        ].value_counts(
            dropna=False
        ).to_string()
    )

    print()
    print(
        "Delay status counts:"
    )

    print(
        results[
            "delay_status"
        ].value_counts(
            dropna=False
        ).to_string()
    )

    valid_count = (
        results[
            "delay_eligibility"
        ]
        .eq("ELIGIBLE")
        .sum()
    )

    print()
    print(
        "Valid delay observations:",
        int(valid_count)
    )

    if valid_count == 0:

        print(
            "No valid realtime delay features "
            "are currently available."
        )

    else:

        valid_delays = results.loc[
            results[
                "delay_eligibility"
            ]
            == "ELIGIBLE",
            "delay_minutes"
        ].dropna()

        if not valid_delays.empty:

            print(
                "Average delay:",
                round(
                    valid_delays.mean(),
                    2
                ),
                "minutes"
            )

            print(
                "Minimum delay:",
                round(
                    valid_delays.min(),
                    2
                ),
                "minutes"
            )

            print(
                "Maximum delay:",
                round(
                    valid_delays.max(),
                    2
                ),
                "minutes"
            )


# =========================================================
# SAVE
# =========================================================

def save_results(
    results
):

    os.makedirs(
        os.path.dirname(
            OUTPUT_FILE
        ),
        exist_ok=True
    )

    results.to_csv(
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
        "VALIDATED REALTIME DELAY FEATURES"
    )
    print(
        "========================================"
    )

    # ---------------------------------------------
    # Load datasets
    # ---------------------------------------------

    realtime = load_realtime()

    quality = load_quality()

    movement = load_movement()

    stops = load_stops()

    stop_times = load_stop_times()

    # ---------------------------------------------
    # Prepare GTFS
    # ---------------------------------------------

    stop_times = prepare_gtfs(
        stop_times,
        stops
    )

    # ---------------------------------------------
    # Generate features
    # ---------------------------------------------

    results = process_observations(
        realtime,
        quality,
        movement,
        stop_times
    )

    # ---------------------------------------------
    # Summary
    # ---------------------------------------------

    print_summary(
        results
    )

    # ---------------------------------------------
    # Display results
    # ---------------------------------------------

    print()
    print(
        "========================================"
    )
    print(
        "VALIDATED FEATURE RESULTS"
    )
    print(
        "========================================"
    )

    if not results.empty:

        print(
            results.to_string(
                index=False
            )
        )

    # ---------------------------------------------
    # Save
    # ---------------------------------------------

    save_results(
        results
    )

    print()
    print(
        "Validated realtime delay feature "
        "generation completed successfully!"
    )


# =========================================================
# RUN
# =========================================================

if __name__ == "__main__":
    main()