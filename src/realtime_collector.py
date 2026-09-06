import os
import time
from datetime import datetime, timezone

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

OUTPUT_FILE = "data/realtime/vline_vehicle_history.csv"

# Collect every 60 seconds
COLLECTION_INTERVAL = 60


# =========================================================
# CHECK API KEY
# =========================================================

if not API_KEY:
    raise RuntimeError(
        "API key not found. Please set the "
        "TRANSPORT_VICTORIA_API_KEY environment variable."
    )


# =========================================================
# CREATE OUTPUT DIRECTORY
# =========================================================

os.makedirs("data/realtime", exist_ok=True)


# =========================================================
# FETCH REALTIME FEED
# =========================================================

def fetch_realtime_feed():

    response = requests.get(
        API_URL,
        headers={
            "KeyID": API_KEY,
            "Cache-Control": "no-cache"
        },
        params={
            "t": str(time.time())
        },
        timeout=30
    )

    response.raise_for_status()

    feed = gtfs_realtime_pb2.FeedMessage()

    feed.ParseFromString(response.content)

    return feed


# =========================================================
# EXTRACT VEHICLE DATA
# =========================================================

def extract_vehicle_data(feed):

    observations = []

    collection_time = datetime.now(
        timezone.utc
    ).isoformat()

    feed_timestamp = None

    if feed.header.HasField("timestamp"):
        feed_timestamp = feed.header.timestamp

    for entity in feed.entity:

        if not entity.HasField("vehicle"):
            continue

        vehicle = entity.vehicle

        # -------------------------------------------------
        # Vehicle ID
        # -------------------------------------------------

        vehicle_id = ""

        if vehicle.HasField("vehicle"):
            vehicle_id = vehicle.vehicle.id

        # -------------------------------------------------
        # Trip ID
        # -------------------------------------------------

        trip_id = ""

        if vehicle.HasField("trip"):
            trip_id = vehicle.trip.trip_id

        # -------------------------------------------------
        # Route ID
        # -------------------------------------------------

        route_id = ""

        if vehicle.HasField("trip"):
            route_id = vehicle.trip.route_id

        # -------------------------------------------------
        # GPS position
        # -------------------------------------------------

        latitude = None
        longitude = None

        if vehicle.HasField("position"):

            latitude = vehicle.position.latitude
            longitude = vehicle.position.longitude

        # -------------------------------------------------
        # Vehicle timestamp
        # -------------------------------------------------

        vehicle_timestamp = None

        if vehicle.HasField("timestamp"):
            vehicle_timestamp = vehicle.timestamp

        # -------------------------------------------------
        # Determine freshness
        # -------------------------------------------------

        status = "UNKNOWN"

        if (
            vehicle_timestamp is not None
            and feed_timestamp is not None
        ):

            age_seconds = (
                feed_timestamp
                - vehicle_timestamp
            )

            if age_seconds <= 120:
                status = "FRESH"
            else:
                status = "STALE"

        # -------------------------------------------------
        # Save observation
        # -------------------------------------------------

        observations.append(
            {
                "collection_time": collection_time,
                "vehicle_id": vehicle_id,
                "trip_id": trip_id,
                "route_id": route_id,
                "latitude": latitude,
                "longitude": longitude,
                "vehicle_timestamp": vehicle_timestamp,
                "feed_timestamp": feed_timestamp,
                "status": status
            }
        )

    return observations


# =========================================================
# SAVE OBSERVATIONS
# =========================================================

def save_observations(observations):

    if not observations:
        return

    new_data = pd.DataFrame(observations)

    if os.path.exists(OUTPUT_FILE):

        new_data.to_csv(
            OUTPUT_FILE,
            mode="a",
            header=False,
            index=False
        )

    else:

        new_data.to_csv(
            OUTPUT_FILE,
            index=False
        )


# =========================================================
# MAIN COLLECTION LOOP
# =========================================================

print("========================================")
print("V/LINE REALTIME DATA COLLECTOR")
print("========================================")

print(
    "Collection interval:",
    COLLECTION_INTERVAL,
    "seconds"
)

print(
    "Output file:",
    OUTPUT_FILE
)

print("\nCollector started.")
print("Press Ctrl+C to stop.\n")


try:

    while True:

        collection_start = time.time()

        try:

            # -------------------------------------------------
            # Fetch feed
            # -------------------------------------------------

            feed = fetch_realtime_feed()

            # -------------------------------------------------
            # Extract vehicles
            # -------------------------------------------------

            observations = extract_vehicle_data(feed)

            # -------------------------------------------------
            # Save data
            # -------------------------------------------------

            save_observations(observations)

            # -------------------------------------------------
            # Display results
            # -------------------------------------------------

            print(
                f"[{datetime.now().strftime('%Y-%m-%d %H:%M:%S')}] "
                f"Vehicles collected: {len(observations)}"
            )

            for observation in observations:

                print(
                    f"  Vehicle: "
                    f"{observation['vehicle_id']} | "
                    f"Trip: "
                    f"{observation['trip_id']} | "
                    f"Status: "
                    f"{observation['status']}"
                )

        except requests.RequestException as error:

            print(
                "API request error:",
                error
            )

        except Exception as error:

            print(
                "Processing error:",
                error
            )

        # -----------------------------------------------------
        # Wait until next collection
        # -----------------------------------------------------

        elapsed = (
            time.time()
            - collection_start
        )

        sleep_time = max(
            0,
            COLLECTION_INTERVAL - elapsed
        )

        time.sleep(sleep_time)


except KeyboardInterrupt:

    print("\n")
    print("Collector stopped by user.")
    print("Realtime data collection completed.")