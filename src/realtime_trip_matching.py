import os
import requests
import pandas as pd
from google.transit import gtfs_realtime_pb2


# ---------------------------------------------------------
# SETTINGS
# ---------------------------------------------------------

API_URL = (
    "https://api.opendata.transport.vic.gov.au/"
    "opendata/public-transport/gtfs/realtime/v1/"
    "vline/vehicle-positions"
)

API_KEY = os.getenv("TRANSPORT_VICTORIA_API_KEY")

STATIC_TRIPS = "data/static/trips.txt"


# ---------------------------------------------------------
# CHECK API KEY
# ---------------------------------------------------------

if not API_KEY:
    raise RuntimeError(
        "API key not found. Set the TRANSPORT_VICTORIA_API_KEY "
        "environment variable before running this script."
    )


# ---------------------------------------------------------
# LOAD STATIC GTFS TRIPS
# ---------------------------------------------------------

print("Loading static GTFS trips...")

trips = pd.read_csv(STATIC_TRIPS)

print(f"Static trips loaded: {len(trips)}")


# ---------------------------------------------------------
# FETCH REALTIME V/LINE VEHICLE POSITIONS
# ---------------------------------------------------------

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


# ---------------------------------------------------------
# DECODE GTFS REALTIME PROTOBUF
# ---------------------------------------------------------

feed = gtfs_realtime_pb2.FeedMessage()
feed.ParseFromString(response.content)

print("Realtime feed decoded successfully!")
print("Realtime entities:", len(feed.entity))


# ---------------------------------------------------------
# MATCH REALTIME VEHICLES TO STATIC TRIPS
# ---------------------------------------------------------

results = []

for entity in feed.entity:

    if not entity.HasField("vehicle"):
        continue

    vehicle = entity.vehicle

    trip_id = ""

    if vehicle.HasField("trip"):
        trip_id = vehicle.trip.trip_id

    vehicle_id = ""

    if vehicle.HasField("vehicle"):
        vehicle_id = vehicle.vehicle.id

    latitude = None
    longitude = None

    if vehicle.HasField("position"):
        latitude = vehicle.position.latitude
        longitude = vehicle.position.longitude

    # Find matching static GTFS trip
    match = trips[trips["trip_id"] == trip_id]

    if len(match) > 0:

        trip = match.iloc[0]

        results.append({
            "vehicle_id": vehicle_id,
            "trip_id": trip_id,
            "route_id": trip["route_id"],
            "trip_headsign": trip["trip_headsign"],
            "direction_id": trip["direction_id"],
            "latitude": latitude,
            "longitude": longitude
        })


# ---------------------------------------------------------
# DISPLAY RESULTS
# ---------------------------------------------------------

print("\n========================================")
print("REALTIME → STATIC GTFS MATCHING")
print("========================================")

print("Realtime vehicles with matching trips:", len(results))

if results:

    result_df = pd.DataFrame(results)

    print("\nMatched vehicles:")

    print(
        result_df.to_string(index=False)
    )

    # Save the results
    output_file = "data/realtime/vline_matched_vehicles.csv"

    os.makedirs("data/realtime", exist_ok=True)

    result_df.to_csv(
        output_file,
        index=False
    )

    print("\nSaved results to:")
    print(output_file)

else:

    print("\nNo realtime vehicles matched the static GTFS trips.")

print("\nRealtime trip matching completed successfully!")