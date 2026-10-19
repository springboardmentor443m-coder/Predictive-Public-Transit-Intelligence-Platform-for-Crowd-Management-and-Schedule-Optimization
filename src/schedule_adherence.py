import os
import math
import requests
import pandas as pd
from google.transit import gtfs_realtime_pb2


# =========================================================
# SETTINGS
# =========================================================

API_URL = (
    "https://api.opendata.transport.vic.gov.au/"
    "opendata/public-transport/gtfs/realtime/v1/"
    "vline/vehicle-positions"
)

API_KEY = os.getenv("TRANSPORT_VICTORIA_API_KEY")

TRIPS_FILE = "data/static/trips.txt"
STOPS_FILE = "data/static/stops.txt"
STOP_TIMES_FILE = "data/static/stop_times.txt"


# =========================================================
# CHECK API KEY
# =========================================================

if not API_KEY:
    raise RuntimeError(
        "API key not found. Please set the "
        "TRANSPORT_VICTORIA_API_KEY environment variable "
        "before running this script."
    )


# =========================================================
# LOAD STATIC GTFS DATA
# =========================================================

print("Loading static GTFS data...")

trips = pd.read_csv(TRIPS_FILE)

stops = pd.read_csv(
    STOPS_FILE,
    dtype={"stop_id": str}
)

stop_times = pd.read_csv(
    STOP_TIMES_FILE,
    dtype={
        "trip_id": str,
        "stop_id": str
    }
)

print(f"Trips loaded: {len(trips)}")
print(f"Stops loaded: {len(stops)}")
print(f"Stop times loaded: {len(stop_times)}")


# =========================================================
# FETCH REALTIME V/LINE FEED
# =========================================================

print("\nFetching V/Line realtime vehicle positions...")

headers = {
    "KeyID": API_KEY
}

response = requests.get(
    API_URL,
    headers=headers,
    timeout=30
)

print("HTTP Status:", response.status_code)

response.raise_for_status()


# =========================================================
# DECODE GTFS-REALTIME PROTOBUF
# =========================================================

feed = gtfs_realtime_pb2.FeedMessage()

feed.ParseFromString(response.content)

print("Realtime feed decoded successfully!")
print("Realtime entities:", len(feed.entity))


# =========================================================
# HAVERSINE DISTANCE FUNCTION
# =========================================================

def distance_km(lat1, lon1, lat2, lon2):
    """
    Calculate the approximate distance between two
    latitude/longitude coordinates in kilometres.
    """

    earth_radius = 6371.0

    lat1_rad = math.radians(lat1)
    lat2_rad = math.radians(lat2)

    delta_lat = math.radians(lat2 - lat1)
    delta_lon = math.radians(lon2 - lon1)

    a = (
        math.sin(delta_lat / 2) ** 2
        + math.cos(lat1_rad)
        * math.cos(lat2_rad)
        * math.sin(delta_lon / 2) ** 2
    )

    return (
        earth_radius
        * 2
        * math.asin(math.sqrt(a))
    )


# =========================================================
# PROCESS REALTIME VEHICLES
# =========================================================

results = []

for entity in feed.entity:

    # Ignore entities that don't contain vehicle data
    if not entity.HasField("vehicle"):
        continue

    vehicle = entity.vehicle


    # -----------------------------------------------------
    # VEHICLE ID
    # -----------------------------------------------------

    vehicle_id = ""

    if vehicle.HasField("vehicle"):
        vehicle_id = vehicle.vehicle.id


    # -----------------------------------------------------
    # TRIP ID
    # -----------------------------------------------------

    trip_id = ""

    if vehicle.HasField("trip"):
        trip_id = vehicle.trip.trip_id


    # -----------------------------------------------------
    # GPS POSITION
    # -----------------------------------------------------

    if not vehicle.HasField("position"):
        continue

    latitude = vehicle.position.latitude
    longitude = vehicle.position.longitude


    # We cannot match a vehicle without a trip ID
    if not trip_id:
        continue


    # -----------------------------------------------------
    # FIND MATCHING STATIC TRIP
    # -----------------------------------------------------

    trip_match = trips[
        trips["trip_id"] == trip_id
    ]

    if trip_match.empty:
        continue

    trip = trip_match.iloc[0]


    # -----------------------------------------------------
    # FIND SCHEDULED STOPS FOR THIS TRIP
    # -----------------------------------------------------

    trip_stops = stop_times[
        stop_times["trip_id"] == trip_id
    ].copy()

    if trip_stops.empty:
        continue


    # -----------------------------------------------------
    # ADD STOP NAMES AND COORDINATES
    # -----------------------------------------------------

    trip_stops = trip_stops.merge(
        stops[
            [
                "stop_id",
                "stop_name",
                "stop_lat",
                "stop_lon"
            ]
        ],
        on="stop_id",
        how="left"
    )


    # -----------------------------------------------------
    # REMOVE STOPS WITHOUT COORDINATES
    # -----------------------------------------------------

    trip_stops = trip_stops.dropna(
        subset=[
            "stop_lat",
            "stop_lon"
        ]
    )

    if trip_stops.empty:
        continue


    # -----------------------------------------------------
    # CALCULATE DISTANCE FROM VEHICLE TO EACH STOP
    # -----------------------------------------------------

    trip_stops["distance_km"] = trip_stops.apply(
        lambda row: distance_km(
            latitude,
            longitude,
            row["stop_lat"],
            row["stop_lon"]
        ),
        axis=1
    )


    # -----------------------------------------------------
    # FIND NEAREST STOP
    # -----------------------------------------------------

    nearest = trip_stops.loc[
        trip_stops["distance_km"].idxmin()
    ]


    # -----------------------------------------------------
    # SAVE RESULT
    # -----------------------------------------------------

    results.append(
        {
            "vehicle_id": vehicle_id,
            "trip_id": trip_id,
            "route_id": trip["route_id"],
            "trip_headsign": trip["trip_headsign"],
            "direction_id": trip["direction_id"],
            "current_latitude": latitude,
            "current_longitude": longitude,
            "nearest_stop_id": nearest["stop_id"],
            "nearest_stop_name": nearest["stop_name"],
            "distance_to_stop_km": round(
                nearest["distance_km"],
                3
            ),
            "scheduled_arrival": nearest["arrival_time"],
            "scheduled_departure": nearest["departure_time"],
            "stop_sequence": nearest["stop_sequence"]
        }
    )


# =========================================================
# DISPLAY RESULTS
# =========================================================

print("\n========================================")
print("SCHEDULE ADHERENCE ANALYSIS")
print("========================================")

print(
    "Vehicles matched to scheduled stops:",
    len(results)
)


if results:

    result_df = pd.DataFrame(results)

    print("\nRealtime vehicle and nearest scheduled stop:\n")

    print(
        result_df.to_string(index=False)
    )


    # -----------------------------------------------------
    # SAVE RESULTS
    # -----------------------------------------------------

    output_file = (
        "data/realtime/schedule_adherence.csv"
    )

    os.makedirs(
        "data/realtime",
        exist_ok=True
    )

    result_df.to_csv(
        output_file,
        index=False
    )

    print("\nSaved results to:")
    print(output_file)

else:

    print(
        "\nNo realtime vehicles could be matched "
        "to static GTFS stops."
    )


print(
    "\nSchedule adherence analysis completed successfully!"
)