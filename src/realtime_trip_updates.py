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
    "vline/gtfs-realtime/trip-updates"
)

API_KEY = os.getenv("TV_API_KEY")

OUTPUT_FILE = (
    "data/realtime/vline_trip_updates_history.csv"
)

COLLECTION_INTERVAL_SECONDS = 60


# =========================================================
# VALIDATE API KEY
# =========================================================

def validate_api_key():

    if not API_KEY:
        raise RuntimeError(
            "TV_API_KEY environment variable is not set."
        )


# =========================================================
# FETCH TRIP UPDATES
# =========================================================

def fetch_trip_updates():

    headers = {
        "KeyID": API_KEY
    }

    response = requests.get(
        REALTIME_URL,
        headers=headers,
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
# EXTRACT TRIP UPDATES
# =========================================================

def extract_trip_updates(feed):

    rows = []

    feed_timestamp = None

    if feed.HasField("header"):

        if feed.header.HasField("timestamp"):

            feed_timestamp = (
                feed.header.timestamp
            )

    collection_time = datetime.now(
        timezone.utc
    )

    for entity in feed.entity:

        if not entity.HasField(
            "trip_update"
        ):
            continue

        trip_update = entity.trip_update

        trip_id = ""
        route_id = ""
        direction_id = None
        start_time = ""
        start_date = ""
        schedule_relationship = ""

        if trip_update.HasField("trip"):

            trip = trip_update.trip

            if trip.trip_id:
                trip_id = trip.trip_id

            if trip.route_id:
                route_id = trip.route_id

            if trip.HasField("direction_id"):
                direction_id = trip.direction_id

            if trip.start_time:
                start_time = trip.start_time

            if trip.start_date:
                start_date = trip.start_date

            if trip.HasField(
                "schedule_relationship"
            ):
                schedule_relationship = (
                    str(
                        trip.schedule_relationship
                    )
                )

        trip_timestamp = None

        if trip_update.HasField(
            "timestamp"
        ):
            trip_timestamp = (
                trip_update.timestamp
            )

        # -------------------------------------------------
        # STOP TIME UPDATES
        # -------------------------------------------------

        for stop_update in (
            trip_update.stop_time_update
        ):

            stop_sequence = None
            stop_id = ""
            stop_schedule_relationship = ""

            if stop_update.HasField(
                "stop_sequence"
            ):
                stop_sequence = (
                    stop_update.stop_sequence
                )

            if stop_update.stop_id:
                stop_id = stop_update.stop_id

            if stop_update.HasField(
                "schedule_relationship"
            ):
                stop_schedule_relationship = (
                    str(
                        stop_update.schedule_relationship
                    )
                )

            # ---------------------------------------------
            # ARRIVAL
            # ---------------------------------------------

            arrival_delay = None
            arrival_time = None

            if stop_update.HasField(
                "arrival"
            ):

                arrival = stop_update.arrival

                if arrival.HasField(
                    "delay"
                ):
                    arrival_delay = (
                        arrival.delay
                    )

                if arrival.HasField(
                    "time"
                ):
                    arrival_time = (
                        arrival.time
                    )

            # ---------------------------------------------
            # DEPARTURE
            # ---------------------------------------------

            departure_delay = None
            departure_time = None

            if stop_update.HasField(
                "departure"
            ):

                departure = stop_update.departure

                if departure.HasField(
                    "delay"
                ):
                    departure_delay = (
                        departure.delay
                    )

                if departure.HasField(
                    "time"
                ):
                    departure_time = (
                        departure.time
                    )

            rows.append(
                {
                    "collection_time":
                        collection_time.isoformat(),

                    "feed_timestamp":
                        feed_timestamp,

                    "trip_timestamp":
                        trip_timestamp,

                    "trip_id":
                        trip_id,

                    "route_id":
                        route_id,

                    "direction_id":
                        direction_id,

                    "start_time":
                        start_time,

                    "start_date":
                        start_date,

                    "trip_schedule_relationship":
                        schedule_relationship,

                    "stop_sequence":
                        stop_sequence,

                    "stop_id":
                        stop_id,

                    "stop_schedule_relationship":
                        stop_schedule_relationship,

                    "arrival_delay_seconds":
                        arrival_delay,

                    "departure_delay_seconds":
                        departure_delay,

                    "arrival_time":
                        arrival_time,

                    "departure_time":
                        departure_time
                }
            )

    return rows


# =========================================================
# SAVE DATA
# =========================================================

def save_rows(rows):

    if not rows:
        print(
            "No Trip Updates found."
        )
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

    print(
        f"Trip Update rows saved: "
        f"{len(new_data)}"
    )


# =========================================================
# COLLECT ONE BATCH
# =========================================================

def collect_once():

    feed = fetch_trip_updates()

    print(
        "Trip Updates feed decoded successfully!"
    )

    print(
        "Realtime entities:",
        len(feed.entity)
    )

    rows = extract_trip_updates(
        feed
    )

    save_rows(rows)

    return rows


# =========================================================
# MAIN COLLECTOR
# =========================================================

def main():

    validate_api_key()

    print(
        "========================================"
    )

    print(
        "V/LINE REALTIME TRIP UPDATES COLLECTOR"
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

    print(
        "API key detected."
    )

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

                rows = collect_once()

                print(
                    f"[{datetime.now().strftime('%Y-%m-%d %H:%M:%S')}] "
                    f"Trip Update rows collected: "
                    f"{len(rows)}"
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
            "Trip Update collection completed."
        )


# =========================================================
# RUN
# =========================================================

if __name__ == "__main__":
    main()