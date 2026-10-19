import os
import math
import pandas as pd


# =========================================================
# SETTINGS
# =========================================================

INPUT_FILE = "data/realtime/vline_vehicle_history.csv"

OUTPUT_FILE = "data/realtime/vline_movement_analysis.csv"


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
# LOAD DATA
# =========================================================

print("========================================")
print("REALTIME VEHICLE MOVEMENT ANALYSIS")
print("========================================")

print("\nLoading realtime vehicle history...")

if not os.path.exists(INPUT_FILE):

    raise FileNotFoundError(
        f"Realtime history file not found: {INPUT_FILE}"
    )


df = pd.read_csv(INPUT_FILE)

print("Realtime observations loaded:", len(df))


# =========================================================
# VALIDATE REQUIRED COLUMNS
# =========================================================

required_columns = [
    "collection_time",
    "vehicle_id",
    "trip_id",
    "latitude",
    "longitude",
    "vehicle_timestamp",
    "feed_timestamp",
    "status"
]

missing_columns = [
    column
    for column in required_columns
    if column not in df.columns
]

if missing_columns:

    raise ValueError(
        "Missing required columns: "
        + ", ".join(missing_columns)
    )


# =========================================================
# CLEAN DATA
# =========================================================

df["collection_time"] = pd.to_datetime(
    df["collection_time"],
    errors="coerce"
)

df["latitude"] = pd.to_numeric(
    df["latitude"],
    errors="coerce"
)

df["longitude"] = pd.to_numeric(
    df["longitude"],
    errors="coerce"
)

df["vehicle_timestamp"] = pd.to_numeric(
    df["vehicle_timestamp"],
    errors="coerce"
)

df["feed_timestamp"] = pd.to_numeric(
    df["feed_timestamp"],
    errors="coerce"
)


df = df.dropna(
    subset=[
        "collection_time",
        "vehicle_id",
        "latitude",
        "longitude"
    ]
)


# =========================================================
# SORT OBSERVATIONS
# =========================================================

df = df.sort_values(
    [
        "vehicle_id",
        "trip_id",
        "collection_time"
    ]
).reset_index(drop=True)


# =========================================================
# CALCULATE MOVEMENT
# =========================================================

results = []


for (
    vehicle_id,
    trip_id
), group in df.groupby(
    ["vehicle_id", "trip_id"]
):

    group = group.sort_values(
        "collection_time"
    ).reset_index(drop=True)

    previous_latitude = None
    previous_longitude = None
    previous_time = None

    for _, row in group.iterrows():

        current_latitude = row["latitude"]
        current_longitude = row["longitude"]
        current_time = row["collection_time"]

        distance_km = 0.0
        elapsed_minutes = 0.0
        speed_kmh = 0.0

        movement_status = "FIRST_OBSERVATION"

        # -------------------------------------------------
        # Compare with previous observation
        # -------------------------------------------------

        if (
            previous_latitude is not None
            and previous_longitude is not None
            and previous_time is not None
        ):

            distance_km = haversine_distance(
                previous_latitude,
                previous_longitude,
                current_latitude,
                current_longitude
            )

            elapsed_seconds = (
                current_time - previous_time
            ).total_seconds()

            elapsed_minutes = (
                elapsed_seconds / 60
            )

            # Avoid division by zero
            if elapsed_seconds > 0:

                speed_kmh = (
                    distance_km
                    / (elapsed_seconds / 3600)
                )

            # -------------------------------------------------
            # Movement classification
            # -------------------------------------------------

            if distance_km < 0.01:

                movement_status = "NO_MOVEMENT"

            else:

                movement_status = "MOVING"

        # -------------------------------------------------
        # Store result
        # -------------------------------------------------

        results.append(
            {
                "collection_time":
                    current_time,

                "vehicle_id":
                    vehicle_id,

                "trip_id":
                    trip_id,

                "latitude":
                    current_latitude,

                "longitude":
                    current_longitude,

                "vehicle_timestamp":
                    row["vehicle_timestamp"],

                "feed_timestamp":
                    row["feed_timestamp"],

                "status":
                    row["status"],

                "distance_from_previous_km":
                    round(distance_km, 4),

                "elapsed_from_previous_min":
                    round(elapsed_minutes, 2),

                "estimated_speed_kmh":
                    round(speed_kmh, 2),

                "movement_status":
                    movement_status
            }
        )

        previous_latitude = current_latitude
        previous_longitude = current_longitude
        previous_time = current_time


# =========================================================
# CREATE MOVEMENT DATAFRAME
# =========================================================

movement_df = pd.DataFrame(results)


# =========================================================
# SUMMARY
# =========================================================

print("\n========================================")
print("MOVEMENT ANALYSIS SUMMARY")
print("========================================")

print(
    "Movement observations:",
    len(movement_df)
)

if len(movement_df) > 0:

    movement_counts = (
        movement_df["movement_status"]
        .value_counts()
    )

    print("\nMovement status counts:")

    print(movement_counts.to_string())

    total_distance = (
        movement_df[
            "distance_from_previous_km"
        ].sum()
    )

    print(
        "\nTotal observed distance:",
        round(total_distance, 4),
        "km"
    )

    moving_rows = movement_df[
        movement_df["movement_status"] == "MOVING"
    ]

    if len(moving_rows) > 0:

        average_speed = (
            moving_rows[
                "estimated_speed_kmh"
            ].mean()
        )

        print(
            "Average observed speed:",
            round(average_speed, 2),
            "km/h"
        )

    else:

        print(
            "Average observed speed: "
            "No movement detected"
        )


# =========================================================
# DISPLAY SAMPLE
# =========================================================

print("\nRealtime movement analysis:")

print(
    movement_df.tail(10).to_string(
        index=False
    )
)


# =========================================================
# SAVE RESULTS
# =========================================================

os.makedirs(
    os.path.dirname(OUTPUT_FILE),
    exist_ok=True
)

movement_df.to_csv(
    OUTPUT_FILE,
    index=False
)


print("\nSaved results to:")

print(OUTPUT_FILE)

print(
    "\nRealtime vehicle movement analysis "
    "completed successfully!"
)