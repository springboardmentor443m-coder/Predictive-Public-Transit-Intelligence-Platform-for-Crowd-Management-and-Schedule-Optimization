import os
import time
from datetime import datetime, timezone

import pandas as pd
import requests
from google.transit import gtfs_realtime_pb2


# =========================================================
# SETTINGS
# =========================================================

REALTIME_URL = (
    "https://api.vic.gov.au/transport/"
    "vline/gtfs-realtime/vehicle-positions"
)

OUTPUT_FILE = (
    "data/realtime/vline_vehicle_history.csv"
)

COLLECTION_INTERVAL_SECONDS = 60


# =========================================================
# HELPER FUNCTIONS
# =========================================================

def unix_to_datetime(timestamp):
    """Convert Unix timestamp to UTC datetime."""

    if timestamp is None:
        return None

    try:
        return datetime.fromtimestamp(
            int(timestamp),
            tz=timezone.utc
        )
    except (ValueError, TypeError, OSError):
        return None


def get_vehicle_status(
    vehicle_timestamp,
    previous_timestamp,
    feed_timestamp,
    previous_feed_timestamp
):
    """
    Determine whether the realtime observation is fresh
    or stale.

    A changing vehicle timestamp means the vehicle data
    itself has been updated.

    A changing feed timestamp alone does NOT guarantee that
    the vehicle position has changed.
    """

    if vehicle_timestamp is None:
        return "MISSING_TIMESTAMP"

    if previous_timestamp is None:
        return "FRESH"

    if vehicle_timestamp > previous_timestamp:
        return "FRESH"

    if vehicle_timestamp == previous_timestamp:

        if (
            feed_timestamp is not None
            and previous_feed_timestamp is not None
            and feed_timestamp > previous_feed_timestamp
        ):
            return "STALE_VEHICLE_DATA"

        return "REPEATED_DATA"

    return "OLDER_DATA"


# =========================================================
# FETCH REALTIME FEED
# =========================================================

def fetch_vehicle_positions():

    response = requests.get(
        REALTIME_URL,
        timeout=30
    )

    print(
        f"HTTP Status: {response.status_code}"
    )

    response.raise_for_status()

    feed = gtfs_realtime_pb2.FeedMessage()

    feed.ParseFromString(
        response.content
    )

    return feed


# =========================================================
# EXTRACT VEHICLES
# =========================================================

def extract_vehicles(feed):

    vehicles = []

    for entity in feed.entity:

        if not entity.HasField(
            "vehicle"
        ):
            continue

        vehicle = entity.vehicle

        vehicle_id = ""

        trip_id = ""

        route_id = ""

        latitude = None

        longitude = None

        vehicle_timestamp = None

        # ---------------------------------------------
        # Vehicle ID
        # ---------------------------------------------

        if vehicle.HasField("vehicle"):

            vehicle_id = (
                vehicle.vehicle.id
            )

        # ---------------------------------------------
        # Trip information
        # ---------------------------------------------

        if vehicle.HasField("trip"):

            trip = vehicle.trip

            if trip.trip_id:
                trip_id = trip.trip_id

            if trip.route_id:
                route_id = trip.route_id

        # ---------------------------------------------
        # Position
        # ---------------------------------------------

        if vehicle.HasField("position"):

            position = vehicle.position

            latitude = position.latitude

            longitude = position.longitude

        # ---------------------------------------------
        # Vehicle timestamp
        # ---------------------------------------------

        if vehicle.HasField("timestamp"):

            vehicle_timestamp = (
                vehicle.timestamp
            )

        vehicles.append(
            {
                "vehicle_id": vehicle_id,
                "trip_id": trip_id,
                "route_id": route_id,
                "latitude": latitude,
                "longitude": longitude,
                "vehicle_timestamp":
                    vehicle_timestamp
            }
        )

    return vehicles


# =========================================================
# LOAD EXISTING HISTORY
# =========================================================

def load_existing_history():

    if not os.path.exists(
        OUTPUT_FILE
    ):
        return pd.DataFrame()

    try:

        df = pd.read_csv(
            OUTPUT_FILE
        )

        return df

    except Exception as error:

        print(
            "Warning: could not read existing "
            "history file."
        )

        print(error)

        return pd.DataFrame()


# =========================================================
# FIND PREVIOUS VEHICLE OBSERVATION
# =========================================================

def get_previous_observation(
    history,
    vehicle_id
):

    if history.empty:
        return None

    if "vehicle_id" not in history.columns:
        return None

    vehicle_history = history[
        history["vehicle_id"].astype(str)
        == str(vehicle_id)
    ]

    if vehicle_history.empty:
        return None

    vehicle_history = vehicle_history.sort_values(
        "collection_time"
    )

    return vehicle_history.iloc[-1]


# =========================================================
# COLLECT ONE BATCH
# =========================================================

def collect_once(history):

    feed = fetch_vehicle_positions()

    feed_timestamp = None

    if feed.HasField("header"):

        if feed.header.HasField(
            "timestamp"
        ):

            feed_timestamp = (
                feed.header.timestamp
            )

    print(
        "Realtime feed decoded successfully!"
    )

    print(
        "Realtime entities:",
        len(feed.entity)
    )

    vehicles = extract_vehicles(
        feed
    )

    collection_time = datetime.now(
        timezone.utc
    )

    rows = []

    for vehicle in vehicles:

        vehicle_id = (
            vehicle["vehicle_id"]
        )

        previous = (
            get_previous_observation(
                history,
                vehicle_id
            )
        )

        previous_timestamp = None
        previous_feed_timestamp = None

        if previous is not None:

            if pd.notna(
                previous.get(
                    "vehicle_timestamp"
                )
            ):

                previous_timestamp = int(
                    previous[
                        "vehicle_timestamp"
                    ]
                )

            if pd.notna(
                previous.get(
                    "feed_timestamp"
                )
            ):

                previous_feed_timestamp = int(
                    previous[
                        "feed_timestamp"
                    ]
                )

        status = get_vehicle_status(
            vehicle[
                "vehicle_timestamp"
            ],
            previous_timestamp,
            feed_timestamp,
            previous_feed_timestamp
        )

        vehicle_datetime = (
            unix_to_datetime(
                vehicle[
                    "vehicle_timestamp"
                ]
            )
        )

        rows.append(
            {
                "collection_time":
                    collection_time.isoformat(),

                "vehicle_id":
                    vehicle[
                        "vehicle_id"
                    ],

                "trip_id":
                    vehicle[
                        "trip_id"
                    ],

                "route_id":
                    vehicle[
                        "route_id"
                    ],

                "latitude":
                    vehicle[
                        "latitude"
                    ],

                "longitude":
                    vehicle[
                        "longitude"
                    ],

                "vehicle_timestamp":
                    vehicle[
                        "vehicle_timestamp"
                    ],

                "vehicle_datetime":
                    (
                        vehicle_datetime.isoformat()
                        if vehicle_datetime
                        else None
                    ),

                "feed_timestamp":
                    feed_timestamp,

                "status":
                    status
            }
        )

    return rows


# =========================================================
# SAVE HISTORY
# =========================================================

def save_rows(rows):

    if not rows:
        return

    new_data = pd.DataFrame(
        rows
    )

    os.makedirs(
        os.path.dirname(
            OUTPUT_FILE
        ),
        exist_ok=True
    )

    if os.path.exists(
        OUTPUT_FILE
    ):

        try:

            existing = pd.read_csv(
                OUTPUT_FILE
            )

        except Exception:

            existing = pd.DataFrame()

        combined = pd.concat(
            [
                existing,
                new_data
            ],
            ignore_index=True
        )

    else:

        combined = new_data

    combined.to_csv(
        OUTPUT_FILE,
        index=False
    )


# =========================================================
# MAIN COLLECTOR
# =========================================================

def main():

    print(
        "========================================"
    )

    print(
        "V/LINE REALTIME DATA COLLECTOR"
    )

    print(
        "========================================"
    )

    print(
        f"Collection interval: "
        f"{COLLECTION_INTERVAL_SECONDS} seconds"
    )

    print(
        f"Output file: {OUTPUT_FILE}"
    )

    print()

    history = load_existing_history()

    print(
        "Collector started."
    )

    print(
        "Press Ctrl+C to stop."
    )

    print()

    try:

        while True:

            try:

                rows = collect_once(
                    history
                )

                save_rows(rows)

                # Update in-memory history so the
                # next iteration can compare against
                # the observation collected now.

                if rows:

                    new_rows = pd.DataFrame(
                        rows
                    )

                    history = pd.concat(
                        [
                            history,
                            new_rows
                        ],
                        ignore_index=True
                    )

                print(
                    f"[{datetime.now().strftime('%Y-%m-%d %H:%M:%S')}] "
                    f"Vehicles collected: "
                    f"{len(rows)}"
                )

                for row in rows:

                    print(
                        f"  Vehicle: "
                        f"{row['vehicle_id']} | "
                        f"Trip: "
                        f"{row['trip_id']} | "
                        f"Status: "
                        f"{row['status']}"
                    )

            except Exception as error:

                print(
                    "Collection error:"
                )

                print(error)

            time.sleep(
                COLLECTION_INTERVAL_SECONDS
            )

    except KeyboardInterrupt:

        print()

        print(
            "Collector stopped by user."
        )

        print(
            "Realtime data collection completed."
        )


# =========================================================
# RUN
# =========================================================

if __name__ == "__main__":
    main()