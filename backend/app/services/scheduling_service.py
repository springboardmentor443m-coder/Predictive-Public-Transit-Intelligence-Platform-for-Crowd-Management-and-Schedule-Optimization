
from pathlib import Path

import pandas as pd


# Resolve the repository root from this file:
# backend/app/services/scheduling_service.py
# parents[0] = backend/app/services
# parents[1] = backend/app
# parents[2] = backend
# parents[3] = repository root
PROJECT_ROOT = Path(__file__).resolve().parents[3]
GTFS_PATH = PROJECT_ROOT / "data" / "bmrcl"


def load_gtfs_data():
    """Load and validate GTFS files used by scheduling endpoints."""
    required_files = {
        "routes": "routes.txt",
        "trips": "trips.txt",
        "stop_times": "stop_times.txt",
        "stops": "stops.txt",
        "calendar": "calendar.txt",
        "calendar_dates": "calendar_dates.txt",
        "frequencies": "frequencies.txt",
    }

    if not GTFS_PATH.is_dir():
        raise FileNotFoundError(
            f"GTFS data directory not found: {GTFS_PATH}"
        )

    data = {}

    for key, filename in required_files.items():
        path = GTFS_PATH / filename

        if not path.is_file():
            raise FileNotFoundError(
                f"Required GTFS file not found: {path}"
            )

        try:
            data[key] = pd.read_csv(
                path,
                dtype=str,
                keep_default_na=False,
            )
        except Exception as exc:
            raise RuntimeError(
                f"Could not read GTFS file '{path}': {exc}"
            ) from exc

    # Check required columns before the endpoint logic uses them.
    required_columns = {
        "routes": [
            "route_id",
            "route_short_name",
            "route_long_name",
        ],
        "trips": [
            "route_id",
            "trip_id",
            "service_id",
        ],
        "stop_times": [
            "trip_id",
            "stop_id",
            "stop_sequence",
        ],
        "stops": [
            "stop_id",
            "stop_name",
        ],
        "calendar": [
            "service_id",
            "monday",
            "tuesday",
            "wednesday",
            "thursday",
            "friday",
            "saturday",
            "sunday",
            "start_date",
            "end_date",
        ],
        "calendar_dates": [
            "service_id",
            "date",
            "exception_type",
        ],
        "frequencies": [
            "trip_id",
            "start_time",
            "end_time",
            "headway_secs",
        ],
    }

    for key, columns in required_columns.items():
        missing = [
            column for column in columns
            if column not in data[key].columns
        ]

        if missing:
            raise ValueError(
                f"GTFS file '{required_files[key]}' is missing "
                f"required columns: {missing}"
            )

    return data


def _records(frame):
    """Convert a DataFrame to JSON-friendly records."""
    if frame.empty:
        return []

    clean_frame = frame.astype(object).where(
        pd.notna(frame), None
    )

    # Convert pandas/numpy scalar values to ordinary Python values.
    return clean_frame.to_dict(orient="records")


def _sort_gtfs_times(frame, columns):
    """Sort GTFS time and sequence columns consistently."""
    if frame.empty:
        return frame.copy()

    result = frame.copy()

    sort_columns = [
        column for column in columns
        if column in result.columns
    ]

    if not sort_columns:
        return result.reset_index(drop=True)

    return result.sort_values(
        sort_columns,
        kind="stable",
        na_position="last",
    ).reset_index(drop=True)


def _normalise_date(date):
    """Return a valid pandas Timestamp, or None for invalid dates."""
    parsed = pd.to_datetime(date, errors="coerce")

    if pd.isna(parsed):
        return None

    return parsed.normalize()


def _gtfs_date(value):
    """Convert a GTFS date such as 20260817 to YYYYMMDD."""
    text = str(value).strip()

    if text.endswith(".0"):
        text = text[:-2]

    return text.replace("-", "")


def get_metro_routes():
    """Return available metro routes."""
    data = load_gtfs_data()
    routes = data["routes"]

    result = routes[
        ["route_id", "route_short_name", "route_long_name"]
    ].drop_duplicates(subset=["route_id"])

    return _records(
        result.sort_values("route_id", kind="stable")
    )


def get_route_stations(route_id: str):
    """Return stops used by trips belonging to a route."""
    data = load_gtfs_data()

    trips = data["trips"]
    stop_times = data["stop_times"]
    stops = data["stops"]

    route_trips = trips[
        trips["route_id"] == str(route_id)
    ]

    if route_trips.empty:
        return []

    route_stop_times = stop_times[
        stop_times["trip_id"].isin(route_trips["trip_id"])
    ]

    if route_stop_times.empty:
        return []

    used_stop_ids = route_stop_times["stop_id"].drop_duplicates()

    used_stops = stops[
        stops["stop_id"].isin(used_stop_ids)
    ].copy()

    # Collapse platform-level stops to parent stations when available.
    # Retain the original stop when parent_station is blank or absent.
    if "parent_station" in used_stops.columns:
        parent = used_stops["parent_station"].astype(str).str.strip()

        used_stops["station_id"] = parent.where(
            parent.ne(""),
            used_stops["stop_id"],
        )
    else:
        used_stops["station_id"] = used_stops["stop_id"]

    station_ids = used_stops["station_id"].drop_duplicates()

    # Use the parent station's name where that parent exists in stops.txt.
    station_rows = stops[
        stops["stop_id"].isin(station_ids)
    ][["stop_id", "stop_name"]].drop_duplicates(
        subset=["stop_id"]
    )

    # If a parent station isn't present, fall back to the original stops.
    found_ids = set(station_rows["stop_id"])
    missing_parent_ids = [
        station_id for station_id in station_ids
        if station_id not in found_ids
    ]

    if missing_parent_ids:
        fallback = used_stops[
            used_stops["station_id"].isin(missing_parent_ids)
        ][["stop_id", "stop_name"]]

        station_rows = pd.concat(
            [station_rows, fallback],
            ignore_index=True,
        ).drop_duplicates(subset=["stop_id"])

    return _records(
        station_rows.sort_values("stop_name", kind="stable")
    )




def station_belongs_to_route(route_id: str, station_name: str) -> bool:
    """Check whether a station belongs to the selected GTFS route."""
    if not station_name or not station_name.strip():
        return False

    stations = get_route_stations(route_id)
    requested_name = station_name.strip().casefold()

    return any(
        str(station.get("stop_name", "")).strip().casefold()
        == requested_name
        for station in stations
    )




def get_route_trips(route_id: str):
    """Return trips assigned to a route."""
    data = load_gtfs_data()
    trips = data["trips"]

    route_trips = trips[
        trips["route_id"] == str(route_id)
    ].copy()

    if route_trips.empty:
        return []

    columns = [
        "trip_id",
        "route_id",
        "service_id",
        "trip_headsign",
        "direction_id",
    ]

    result = route_trips.reindex(columns=columns).drop_duplicates(
        subset=["trip_id"]
    )

    sort_columns = [
        column for column in ["direction_id", "trip_id"]
        if column in result.columns
    ]

    return _records(
        result.sort_values(sort_columns, kind="stable")
        if sort_columns else result
    )


def get_trip_schedule(trip_id: str):
    """Return the ordered stop timetable for a trip."""
    data = load_gtfs_data()

    stop_times = data["stop_times"]
    stops = data["stops"]

    trip_stop_times = stop_times[
        stop_times["trip_id"] == str(trip_id)
    ].copy()

    if trip_stop_times.empty:
        return []

    trip_stop_times["stop_sequence"] = pd.to_numeric(
        trip_stop_times["stop_sequence"],
        errors="coerce",
    )

    trip_stop_times = trip_stop_times.dropna(
        subset=["stop_sequence"]
    ).sort_values("stop_sequence", kind="stable")

    stop_columns = ["stop_id", "stop_name"]

    if "parent_station" in stops.columns:
        stop_columns.append("parent_station")

    trip_stop_times = trip_stop_times.merge(
        stops[stop_columns],
        on="stop_id",
        how="left",
        validate="many_to_one",
    )

    columns = [
        "trip_id",
        "stop_id",
        "stop_name",
        "arrival_time",
        "departure_time",
        "stop_sequence",
    ]

    return _records(
        trip_stop_times.reindex(columns=columns)
    )


def get_trip_frequency(trip_id: str):
    """Return frequency intervals for a specific trip."""
    data = load_gtfs_data()
    frequencies = data["frequencies"]

    trip_frequencies = frequencies[
        frequencies["trip_id"] == str(trip_id)
    ].copy()

    if trip_frequencies.empty:
        return []

    trip_frequencies["headway_secs"] = pd.to_numeric(
        trip_frequencies["headway_secs"],
        errors="coerce",
    )

    trip_frequencies["headway_minutes"] = (
        trip_frequencies["headway_secs"] / 60
    )

    trip_frequencies = _sort_gtfs_times(
        trip_frequencies,
        ["start_time", "end_time"],
    )

    columns = [
        "trip_id",
        "start_time",
        "end_time",
        "headway_secs",
        "headway_minutes",
        "exact_times",
    ]

    return _records(trip_frequencies.reindex(columns=columns))


def get_route_frequency(route_id: str):
    """Return frequency intervals for trips on a route."""
    data = load_gtfs_data()

    trips = data["trips"]
    frequencies = data["frequencies"]

    route_trips = trips[
        trips["route_id"] == str(route_id)
    ].copy()

    if route_trips.empty:
        return []

    route_frequencies = frequencies[
        frequencies["trip_id"].isin(route_trips["trip_id"])
    ].copy()

    if route_frequencies.empty:
        return []

    trip_columns = [
        "trip_id",
        "route_id",
        "trip_headsign",
        "direction_id",
    ]

    route_frequencies = route_frequencies.merge(
        route_trips.reindex(columns=trip_columns),
        on="trip_id",
        how="left",
        validate="many_to_one",
    )

    route_frequencies["headway_secs"] = pd.to_numeric(
        route_frequencies["headway_secs"],
        errors="coerce",
    )

    route_frequencies["headway_minutes"] = (
        route_frequencies["headway_secs"] / 60
    )

    # Identical intervals can be valid for different trips.
    # Preserve them rather than hiding legitimate schedule records.
    route_frequencies = _sort_gtfs_times(
        route_frequencies,
        [
            "direction_id",
            "start_time",
            "end_time",
            "trip_id",
        ],
    )

    columns = [
        "trip_id",
        "route_id",
        "trip_headsign",
        "direction_id",
        "start_time",
        "end_time",
        "headway_secs",
        "headway_minutes",
        "exact_times",
    ]

    return _records(route_frequencies.reindex(columns=columns))


def get_trip_service(trip_id: str):
    """Return the regular calendar definition for a trip."""
    data = load_gtfs_data()

    trips = data["trips"]
    calendar = data["calendar"]

    trip = trips[trips["trip_id"] == str(trip_id)]

    if trip.empty:
        return []

    service_id = trip.iloc[0]["service_id"]

    service = calendar[
        calendar["service_id"] == service_id
    ]

    columns = [
        "service_id",
        "monday",
        "tuesday",
        "wednesday",
        "thursday",
        "friday",
        "saturday",
        "sunday",
        "start_date",
        "end_date",
    ]

    return _records(service.reindex(columns=columns))


def get_trip_service_dates(trip_id: str):
    """Return regular service and date-specific exceptions for a trip."""
    data = load_gtfs_data()

    trips = data["trips"]
    calendar = data["calendar"]
    calendar_dates = data["calendar_dates"]

    trip = trips[trips["trip_id"] == str(trip_id)]

    if trip.empty:
        return {
            "service_id": None,
            "regular_service": [],
            "service_exceptions": [],
        }

    service_id = trip.iloc[0]["service_id"]

    service_calendar = calendar[
        calendar["service_id"] == service_id
    ]

    service_exceptions = calendar_dates[
        calendar_dates["service_id"] == service_id
    ].copy()

    if not service_exceptions.empty:
        service_exceptions["_sort_date"] = (
            service_exceptions["date"].map(_gtfs_date)
        )
        service_exceptions = service_exceptions.sort_values(
            "_sort_date",
            kind="stable",
        ).drop(columns=["_sort_date"])

    return {
        "service_id": service_id,
        "regular_service": _records(service_calendar),
        "service_exceptions": _records(service_exceptions),
    }


def is_trip_active_on_date(trip_id: str, date: str):
    """Check if a trip runs on a date using GTFS calendar rules."""
    data = load_gtfs_data()

    trips = data["trips"]
    calendar = data["calendar"]
    calendar_dates = data["calendar_dates"]

    trip = trips[trips["trip_id"] == str(trip_id)]

    if trip.empty:
        return False

    requested_date = _normalise_date(date)

    if requested_date is None:
        return False

    service_id = trip.iloc[0]["service_id"]
    requested_gtfs_date = requested_date.strftime("%Y%m%d")

    # GTFS calendar_dates exception_type:
    # 1 = service added, 2 = service removed.
    exceptions = calendar_dates[
        (calendar_dates["service_id"] == service_id)
        & (
            calendar_dates["date"].map(_gtfs_date)
            == requested_gtfs_date
        )
    ]

    if not exceptions.empty:
        exception_type = pd.to_numeric(
            exceptions.iloc[-1]["exception_type"],
            errors="coerce",
        )

        if exception_type == 1:
            return True

        if exception_type == 2:
            return False

    service = calendar[
        calendar["service_id"] == service_id
    ]

    if service.empty:
        # Some GTFS feeds may define service using calendar_dates only.
        return False

    row = service.iloc[0]

    start_date = pd.to_datetime(
        _gtfs_date(row["start_date"]),
        format="%Y%m%d",
        errors="coerce",
    )

    end_date = pd.to_datetime(
        _gtfs_date(row["end_date"]),
        format="%Y%m%d",
        errors="coerce",
    )

    if (
        pd.isna(start_date)
        or pd.isna(end_date)
        or not (start_date <= requested_date <= end_date)
    ):
        return False

    day_name = requested_date.day_name().lower()

    return pd.to_numeric(
        row.get(day_name, 0),
        errors="coerce",
    ) == 1
