import pandas as pd


GTFS_PATH = "../data/bmrcl"


def load_gtfs_data():
    routes = pd.read_csv(f"{GTFS_PATH}/routes.txt")
    trips = pd.read_csv(f"{GTFS_PATH}/trips.txt")
    stop_times = pd.read_csv(f"{GTFS_PATH}/stop_times.txt")
    stops = pd.read_csv(f"{GTFS_PATH}/stops.txt")
    calendar = pd.read_csv(f"{GTFS_PATH}/calendar.txt")
    calendar_dates = pd.read_csv(f"{GTFS_PATH}/calendar_dates.txt")
    frequencies = pd.read_csv(f"{GTFS_PATH}/frequencies.txt")

    return {
        "routes": routes,
        "trips": trips,
        "stop_times": stop_times,
        "stops": stops,
        "calendar": calendar,
        "calendar_dates": calendar_dates,
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


def get_route_trips(route_id: str):
    data = load_gtfs_data()

    trips = data["trips"]

    route_trips = trips[
        trips["route_id"] == route_id
    ]

    return route_trips[
        ["trip_id", "route_id", "service_id", "trip_headsign", "direction_id"]
    ].to_dict(orient="records")


def get_trip_schedule(trip_id: str):
    data = load_gtfs_data()

    stop_times = data["stop_times"]
    stops = data["stops"]

    trip_stop_times = stop_times[
        stop_times["trip_id"] == trip_id
    ].copy()

    trip_stop_times = trip_stop_times.sort_values(
        "stop_sequence"
    )

    trip_stop_times = trip_stop_times.merge(
        stops[
            ["stop_id", "stop_name", "parent_station"]
        ],
        on="stop_id",
        how="left"
    )

    return trip_stop_times[
        [
            "trip_id",
            "stop_id",
            "stop_name",
            "arrival_time",
            "departure_time",
            "stop_sequence"
        ]
    ].to_dict(
        orient="records"
    )


def get_trip_frequency(trip_id: str):
    data = load_gtfs_data()

    frequencies = data["frequencies"]

    trip_frequencies = frequencies[
        frequencies["trip_id"] == trip_id
    ].copy()

    trip_frequencies["headway_minutes"] = (
        trip_frequencies["headway_secs"] / 60
    )

    return trip_frequencies[
        [
            "trip_id",
            "start_time",
            "end_time",
            "headway_secs",
            "headway_minutes",
            "exact_times"
        ]
    ].to_dict(
        orient="records"
    )


def get_route_frequency(route_id: str):
    data = load_gtfs_data()

    trips = data["trips"]
    frequencies = data["frequencies"]

    route_trips = trips[
        trips["route_id"] == route_id
    ]

    route_frequencies = frequencies[
        frequencies["trip_id"].isin(route_trips["trip_id"])
    ].copy()

    route_frequencies = route_frequencies.merge(
        route_trips[
            ["trip_id", "route_id", "trip_headsign", "direction_id"]
        ],
        on="trip_id",
        how="left"
    )

    route_frequencies["headway_minutes"] = (
        route_frequencies["headway_secs"] / 60
    )

    return route_frequencies[
        [
            "trip_id",
            "route_id",
            "trip_headsign",
            "direction_id",
            "start_time",
            "end_time",
            "headway_secs",
            "headway_minutes",
            "exact_times"
        ]
    ].to_dict(
        orient="records"
    )



def get_trip_service(trip_id: str):
    data = load_gtfs_data()

    trips = data["trips"]
    calendar = data["calendar"]

    trip = trips[
        trips["trip_id"] == trip_id
    ]

    if trip.empty:
        return []

    service_id = trip.iloc[0]["service_id"]

    service = calendar[
        calendar["service_id"] == service_id
    ]

    return service[
        [
            "service_id",
            "monday",
            "tuesday",
            "wednesday",
            "thursday",
            "friday",
            "saturday",
            "sunday",
            "start_date",
            "end_date"
        ]
    ].to_dict(
        orient="records"
    )




def get_trip_service_dates(trip_id: str):
    data = load_gtfs_data()

    trips = data["trips"]
    calendar = data["calendar"]
    calendar_dates = data["calendar_dates"]

    trip = trips[
        trips["trip_id"] == trip_id
    ]

    if trip.empty:
        return []

    service_id = trip.iloc[0]["service_id"]

    service_calendar = calendar[
        calendar["service_id"] == service_id
    ]

    service_exceptions = calendar_dates[
        calendar_dates["service_id"] == service_id
    ]

    return {
        "service_id": service_id,
        "regular_service": service_calendar.to_dict(
            orient="records"
        ),
        "service_exceptions": service_exceptions.to_dict(
            orient="records"
        )
    }



def is_trip_active_on_date(trip_id: str, date: str):
    data = load_gtfs_data()

    trips = data["trips"]
    calendar = data["calendar"]
    calendar_dates = data["calendar_dates"]

    trip = trips[
        trips["trip_id"] == trip_id
    ]

    if trip.empty:
        return False

    service_id = trip.iloc[0]["service_id"]

    # Check special date exceptions first
    exception = calendar_dates[
        (calendar_dates["service_id"] == service_id) &
        (calendar_dates["date"].astype(str) == date.replace("-", ""))
    ]

    if not exception.empty:
        exception_type = exception.iloc[0]["exception_type"]

        # 1 = service added
        if exception_type == 1:
            return True

        # 2 = service removed
        if exception_type == 2:
            return False

    # Check regular weekly service
    service = calendar[
        calendar["service_id"] == service_id
    ]

    if service.empty:
        return False

    service = service.iloc[0]

    requested_date = pd.to_datetime(date)

    day_name = requested_date.day_name().lower()

    if service[day_name] == 1:
        return True

    return False