import pandas as pd


GTFS_PATH = "../data/bmrcl"


def load_gtfs_data():
    routes = pd.read_csv(f"{GTFS_PATH}/routes.txt")
    trips = pd.read_csv(f"{GTFS_PATH}/trips.txt")
    stop_times = pd.read_csv(f"{GTFS_PATH}/stop_times.txt")
    stops = pd.read_csv(f"{GTFS_PATH}/stops.txt")
    calendar = pd.read_csv(f"{GTFS_PATH}/calendar.txt")
    frequencies = pd.read_csv(f"{GTFS_PATH}/frequencies.txt")

    return {
        "routes": routes,
        "trips": trips,
        "stop_times": stop_times,
        "stops": stops,
        "calendar": calendar,
        "frequencies": frequencies
    }


def get_metro_routes():
    data = load_gtfs_data()

    routes = data["routes"]

    return routes[
        ["route_id", "route_short_name", "route_long_name"]
    ].to_dict(orient="records")



def get_route_stations(route_id: str):
    data = load_gtfs_data()

    trips = data["trips"]
    stop_times = data["stop_times"]
    stops = data["stops"]

    route_trips = trips[
        trips["route_id"] == route_id
    ]

    route_stop_times = stop_times[
        stop_times["trip_id"].isin(route_trips["trip_id"])
    ]

    platform_stops = stops[
        stops["stop_id"].isin(route_stop_times["stop_id"])
    ]

    station_ids = platform_stops["parent_station"].dropna().unique()

    route_stations = stops[
        stops["stop_id"].isin(station_ids)
    ]

    return route_stations[
        ["stop_id", "stop_name"]
    ].drop_duplicates().to_dict(
        orient="records"
    )