import os
import math
import pandas as pd


# =========================================================
# SETTINGS
# =========================================================

REALTIME_FILE = (
    "data/realtime/vline_vehicle_history.csv"
)

STATIC_STOPS_FILE = (
    "data/static/stops.txt"
)

STATIC_STOP_TIMES_FILE = (
    "data/static/stop_times.txt"
)

OUTPUT_FILE = (
    "data/realtime/schedule_delay_estimation.csv"
)

# Maximum distance at which we consider a vehicle
# to be close enough to a scheduled stop.
STOP_MATCH_THRESHOLD_KM = 1.0

# Delay tolerance.
# Within +/- 2 minutes is considered on time.
DELAY_TOLERANCE_MINUTES = 2.0


# =========================================================
# GTFS TIME → SECONDS
# =========================================================

def gtfs_time_to_seconds(time_value):
    """
    Convert GTFS time such as:

        07:35:00
        24:10:00
        25:23:00

    into seconds from the beginning of the GTFS service day.

    GTFS permits hours greater than 23.
    """

    if pd.isna(time_value):
        return None

    try:
        parts = str(time_value).strip().split(":")

        if len(parts) != 3:
            return None

        hours = int(parts[0])
        minutes = int(parts[1])
        seconds = int(float(parts[2]))

        if minutes < 0 or minutes >= 60:
            return None

        if seconds < 0 or seconds >= 60:
            return None

        return (
            hours * 3600
            + minutes * 60
            + seconds
        )

    except (ValueError, TypeError):
        return None


# =========================================================
# HAVERSINE DISTANCE
# =========================================================

def haversine_distance(
    lat1,
    lon1,
    lat2,
    lon2
):
    """
    Calculate distance between two GPS coordinates
    in kilometres.
    """

    earth_radius_km = 6371.0

    lat1 = math.radians(lat1)
    lon1 = math.radians(lon1)

    lat2 = math.radians(lat2)
    lon2 = math.radians(lon2)

    dlat = lat2 - lat1
    dlon = lon2 - lon1

    a = (
        math.sin(dlat / 2) ** 2
        + math.cos(lat1)
        * math.cos(lat2)
        * math.sin(dlon / 2) ** 2
    )

    c = 2 * math.atan2(
        math.sqrt(a),
        math.sqrt(1 - a)
    )

    return earth_radius_km * c


# =========================================================
# FORMAT GTFS TIME
# =========================================================

def seconds_to_gtfs_time(total_seconds):
    """
    Convert seconds back to HH:MM:SS.

    Hours are allowed to exceed 23.
    """

    if total_seconds is None:
        return None

    total_seconds = int(total_seconds)

    hours = total_seconds // 3600

    remainder = total_seconds % 3600

    minutes = remainder // 60

    seconds = remainder % 60

    return (
        f"{hours:02d}:"
        f"{minutes:02d}:"
        f"{seconds:02d}"
    )


# =========================================================
# FIND CLOSEST SCHEDULED TIME
# =========================================================

def find_closest_scheduled_time(
    observed_seconds,
    scheduled_seconds
):
    """
    Compare an observed clock time with a GTFS scheduled time.

    Because GTFS allows values such as 24:10 and 25:23,
    compare against neighbouring service-day positions.

    Returns:

        closest scheduled seconds
        difference in seconds
    """

    candidates = []

    for day_offset in [-1, 0, 1]:

        candidate = (
            scheduled_seconds
            + day_offset * 86400
        )

        difference = (
            observed_seconds
            - candidate
        )

        candidates.append(
            (
                abs(difference),
                candidate,
                difference
            )
        )

    candidates.sort(
        key=lambda item: item[0]
    )

    _, closest, difference = candidates[0]

    return closest, difference


# =========================================================
# LOAD REALTIME DATA
# =========================================================

print("========================================")
print("SCHEDULE DELAY ESTIMATION")
print("========================================")

print("\nLoading realtime vehicle history...")

if not os.path.exists(REALTIME_FILE):

    raise FileNotFoundError(
        f"Realtime file not found: {REALTIME_FILE}"
    )


realtime = pd.read_csv(
    REALTIME_FILE
)

print(
    "Realtime observations loaded:",
    len(realtime)
)


# =========================================================
# LOAD STATIC STOPS
# =========================================================

print("\nLoading static GTFS stops...")

if not os.path.exists(STATIC_STOPS_FILE):

    raise FileNotFoundError(
        f"Stops file not found: {STATIC_STOPS_FILE}"
    )


stops = pd.read_csv(
    STATIC_STOPS_FILE,
    dtype={
        "stop_id": str
    }
)

print(
    "Static stops loaded:",
    len(stops)
)


# =========================================================
# LOAD STOP TIMES
# =========================================================

print("\nLoading static GTFS stop times...")

if not os.path.exists(STATIC_STOP_TIMES_FILE):

    raise FileNotFoundError(
        f"Stop times file not found: "
        f"{STATIC_STOP_TIMES_FILE}"
    )


stop_times = pd.read_csv(
    STATIC_STOP_TIMES_FILE,
    dtype={
        "trip_id": str,
        "stop_id": str
    }
)

print(
    "Static stop times loaded:",
    len(stop_times)
)


# =========================================================
# VALIDATE REALTIME COLUMNS
# =========================================================

required_realtime_columns = [
    "collection_time",
    "vehicle_id",
    "trip_id",
    "latitude",
    "longitude",
    "vehicle_timestamp",
    "feed_timestamp",
    "status"
]

for column in required_realtime_columns:

    if column not in realtime.columns:

        raise ValueError(
            f"Missing realtime column: {column}"
        )


# =========================================================
# VALIDATE STOP COLUMNS
# =========================================================

required_stop_columns = [
    "stop_id",
    "stop_name",
    "stop_lat",
    "stop_lon"
]

for column in required_stop_columns:

    if column not in stops.columns:

        raise ValueError(
            f"Missing stops column: {column}"
        )


# =========================================================
# VALIDATE STOP-TIME COLUMNS
# =========================================================

required_stop_time_columns = [
    "trip_id",
    "arrival_time",
    "departure_time",
    "stop_id",
    "stop_sequence"
]

for column in required_stop_time_columns:

    if column not in stop_times.columns:

        raise ValueError(
            f"Missing stop_times column: {column}"
        )


# =========================================================
# CLEAN REALTIME DATA
# =========================================================

realtime["collection_time"] = pd.to_datetime(
    realtime["collection_time"],
    errors="coerce",
    utc=True
)

realtime["latitude"] = pd.to_numeric(
    realtime["latitude"],
    errors="coerce"
)

realtime["longitude"] = pd.to_numeric(
    realtime["longitude"],
    errors="coerce"
)

realtime["vehicle_timestamp"] = pd.to_numeric(
    realtime["vehicle_timestamp"],
    errors="coerce"
)

realtime["feed_timestamp"] = pd.to_numeric(
    realtime["feed_timestamp"],
    errors="coerce"
)

realtime["vehicle_id"] = (
    realtime["vehicle_id"]
    .astype(str)
    .str.strip()
)

realtime["trip_id"] = (
    realtime["trip_id"]
    .astype(str)
    .str.strip()
)


realtime = realtime.dropna(
    subset=[
        "collection_time",
        "vehicle_id",
        "trip_id",
        "latitude",
        "longitude"
    ]
)


# =========================================================
# CLEAN STATIC STOPS
# =========================================================

stops["stop_id"] = (
    stops["stop_id"]
    .astype(str)
    .str.strip()
)

stops["stop_lat"] = pd.to_numeric(
    stops["stop_lat"],
    errors="coerce"
)

stops["stop_lon"] = pd.to_numeric(
    stops["stop_lon"],
    errors="coerce"
)

stops = stops.dropna(
    subset=[
        "stop_id",
        "stop_lat",
        "stop_lon"
    ]
)


# =========================================================
# CLEAN STOP TIMES
# =========================================================

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

stop_times["arrival_seconds"] = (
    stop_times["arrival_time"]
    .apply(gtfs_time_to_seconds)
)

stop_times["departure_seconds"] = (
    stop_times["departure_time"]
    .apply(gtfs_time_to_seconds)
)

stop_times["stop_sequence"] = pd.to_numeric(
    stop_times["stop_sequence"],
    errors="coerce"
)


stop_times = stop_times.dropna(
    subset=[
        "trip_id",
        "stop_id",
        "arrival_seconds",
        "departure_seconds",
        "stop_sequence"
    ]
)


# =========================================================
# STOP LOOKUP
# =========================================================

stop_lookup = stops[
    [
        "stop_id",
        "stop_name",
        "stop_lat",
        "stop_lon"
    ]
].drop_duplicates(
    subset=["stop_id"]
)


# =========================================================
# PROCESS REALTIME OBSERVATIONS
# =========================================================

results = []


for _, vehicle in realtime.iterrows():

    trip_id = vehicle["trip_id"]

    vehicle_id = vehicle["vehicle_id"]

    latitude = vehicle["latitude"]

    longitude = vehicle["longitude"]

    collection_time = vehicle["collection_time"]

    # -----------------------------------------------------
    # Get scheduled stops for this trip
    # -----------------------------------------------------

    trip_stops = stop_times[
        stop_times["trip_id"] == trip_id
    ].copy()

    if trip_stops.empty:

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

                "nearest_stop_id":
                    None,

                "nearest_stop_name":
                    None,

                "distance_to_stop_km":
                    None,

                "scheduled_arrival":
                    None,

                "scheduled_departure":
                    None,

                "stop_sequence":
                    None,

                "observed_time":
                    collection_time.strftime(
                        "%H:%M:%S"
                    ),

                "delay_minutes":
                    None,

                "delay_status":
                    "NO_STATIC_TRIP_MATCH"
            }
        )

        continue

    # -----------------------------------------------------
    # Join stop coordinates
    # -----------------------------------------------------

    trip_stops = trip_stops.merge(
        stop_lookup,
        on="stop_id",
        how="left"
    )

    trip_stops = trip_stops.dropna(
        subset=[
            "stop_lat",
            "stop_lon"
        ]
    )

    if trip_stops.empty:

        continue

    # -----------------------------------------------------
    # Calculate distance to each scheduled stop
    # -----------------------------------------------------

    trip_stops["distance_km"] = trip_stops.apply(
        lambda row: haversine_distance(
            latitude,
            longitude,
            row["stop_lat"],
            row["stop_lon"]
        ),
        axis=1
    )

    # -----------------------------------------------------
    # Find nearest stop
    # -----------------------------------------------------

    nearest_index = (
        trip_stops["distance_km"]
        .idxmin()
    )

    nearest_stop = trip_stops.loc[
        nearest_index
    ]

    nearest_stop_id = (
        nearest_stop["stop_id"]
    )

    nearest_stop_name = (
        nearest_stop["stop_name"]
    )

    distance_to_stop = (
        float(nearest_stop["distance_km"])
    )

    scheduled_arrival = (
        nearest_stop["arrival_time"]
    )

    scheduled_departure = (
        nearest_stop["departure_time"]
    )

    stop_sequence = int(
        nearest_stop["stop_sequence"]
    )

    scheduled_seconds = int(
        nearest_stop["arrival_seconds"]
    )

    # -----------------------------------------------------
    # Determine observed time
    #
    # IMPORTANT:
    # Use the realtime vehicle timestamp when available.
    # This is better than using our local collection time.
    # -----------------------------------------------------

    vehicle_timestamp = (
        vehicle["vehicle_timestamp"]
    )

    if pd.notna(vehicle_timestamp):

        observed_datetime = (
            pd.to_datetime(
                vehicle_timestamp,
                unit="s",
                utc=True
            )
        )

    else:

        observed_datetime = collection_time

    observed_seconds = (
        observed_datetime.hour * 3600
        + observed_datetime.minute * 60
        + observed_datetime.second
    )

    # -----------------------------------------------------
    # Compare observed and scheduled times
    # -----------------------------------------------------

    closest_scheduled_seconds, difference = (
        find_closest_scheduled_time(
            observed_seconds,
            scheduled_seconds
        )
    )

    raw_delay_minutes = (
        difference / 60.0
    )

    # -----------------------------------------------------
    # Do NOT calculate a delay unless the vehicle is
    # sufficiently close to a scheduled stop.
    #
    # Our current GPS is ~0.788 km from Marshall Station,
    # so it qualifies geographically, but we still need
    # to be careful because GPS proximity alone does not
    # prove arrival/departure at that stop.
    # -----------------------------------------------------

    if distance_to_stop > STOP_MATCH_THRESHOLD_KM:

        delay_minutes = None

        delay_status = (
            "INSUFFICIENT_REALTIME_DATA"
        )

    else:

        # -------------------------------------------------
        # Additional protection against unrealistic values.
        #
        # A delay calculation with a difference of several
        # hours indicates that the service-day relationship
        # cannot be confidently established.
        # -------------------------------------------------

        if abs(raw_delay_minutes) > 180:

            delay_minutes = None

            delay_status = (
                "INSUFFICIENT_REALTIME_DATA"
            )

        else:

            delay_minutes = round(
                raw_delay_minutes,
                2
            )

            if (
                delay_minutes
                > DELAY_TOLERANCE_MINUTES
            ):

                delay_status = "DELAYED"

            elif (
                delay_minutes
                < -DELAY_TOLERANCE_MINUTES
            ):

                delay_status = "EARLY"

            else:

                delay_status = "ON_TIME"

    # -----------------------------------------------------
    # Store result
    # -----------------------------------------------------

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

            "nearest_stop_id":
                nearest_stop_id,

            "nearest_stop_name":
                nearest_stop_name,

            "distance_to_stop_km":
                round(
                    distance_to_stop,
                    4
                ),

            "scheduled_arrival":
                scheduled_arrival,

            "scheduled_departure":
                scheduled_departure,

            "stop_sequence":
                stop_sequence,

            "observed_time":
                observed_datetime.strftime(
                    "%H:%M:%S"
                ),

            "delay_minutes":
                delay_minutes,

            "delay_status":
                delay_status
        }
    )


# =========================================================
# CREATE RESULT DATAFRAME
# =========================================================

delay_df = pd.DataFrame(results)


# =========================================================
# SUMMARY
# =========================================================

print("\n========================================")
print("DELAY ESTIMATION SUMMARY")
print("========================================")

print(
    "Observations analysed:",
    len(delay_df)
)


if not delay_df.empty:

    print("\nDelay status counts:")

    print(
        delay_df[
            "delay_status"
        ]
        .value_counts()
        .to_string()
    )

    print("\nResults:")

    print(
        delay_df.tail(15).to_string(
            index=False
        )
    )


# =========================================================
# SAVE
# =========================================================

os.makedirs(
    os.path.dirname(OUTPUT_FILE),
    exist_ok=True
)

delay_df.to_csv(
    OUTPUT_FILE,
    index=False
)


print("\nSaved results to:")

print(OUTPUT_FILE)

print(
    "\nSchedule delay estimation "
    "completed successfully!"
)