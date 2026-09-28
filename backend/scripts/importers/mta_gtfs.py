"""MTA GTFS station-network importer.

Turns the official NYC subway GTFS feed into ``stations.csv`` — real MTA parent
stop ids, stop names, coordinates, the trunk-route family each stop is grouped
into, and a modelled platform capacity.

The feed (https://www.mta.info/developers/data, ``nyct/subway/google_transit.zip``)
ships ``stops.txt`` / ``routes.txt`` / ``trips.txt`` / ``stop_times.txt``. Three
details make the extraction non-obvious:

1. **Parent vs child stops.** A physical station complex ("Times Sq-42 St") is a
   ``location_type=1`` row whose id is the station code the app uses; each
   platform ("Times Sq-42 St" N/S/E/M platforms) is a child row carrying a
   ``parent_station`` pointer and a ``N``/``S`` direction suffix.
2. **Stop names are not unique.** ``"86 St"`` exists on the 1/2/3 (86 St, code
   ``620``), the 4/5/6 (``626``) and the N/Q/R/W (``631``-area) trunk, and
   ``"Bedford Av"`` is both an IRT stop and an IND one. Selection is therefore by
   curated station name, and among the matching complexes the busiest platform
   (by weekday peak arrivals) wins, so the code matches the dominant service.
3. **Service frequency drives capacity.** Weekday 07:00-09:00 arrivals at the
   selected complex, halved for the two directions, give trains/hour; capacity
   is that frequency at a modelled 180 riders per train, rounded to 50.

Usage::

    python scripts/importers/cli.py --city mta-gtfs --input <gtfs-dir>

Output columns: ``code,name,line,capacity_per_hour,lat,lng,services,trains_per_hour``.
"""

import csv
import os
from collections import defaultdict

STATION_COLUMNS = [
    "code", "name", "line", "capacity_per_hour", "lat", "lng",
    "services", "trains_per_hour",
]

# Curated station complexes: one entry per physical stop the demo tracks,
# spanning every trunk so no borough or service family is unrepresented.
CURATED_STATIONS = [
    # 1/2/3 — Broadway–Seventh Avenue
    "Times Sq-42 St", "Grand Central-42 St", "34 St-Penn Station",
    "42 St-Bryant Pk", "42 St-Port Authority Bus Terminal", "14 St-Union Sq",
    "59 St-Columbus Circle", "86 St", "96 St", "125 St", "72 St", "Chambers St",
    "Wall St", "Bowling Green", "168 St", "181 St", "190 St",
    "Atlantic Av-Barclays Ctr", "Nevins St", "Borough Hall", "4 Av-9 St",
    "Prospect Av", "Church Av", "Flatbush Av-Brooklyn College", "Bedford Av",
    "Jay St-MetroTech", "Fulton St", "67 Av", "Queensboro Plaza",
    "Jackson Hts-Roosevelt Av", "Forest Hills-71 Av", "Flushing-Main St",
    "Jamaica Center-Parsons/Archer", "Howard Beach-JFK Airport",
    "61 St-Woodside", "138 St-Grand Concourse", "161 St-Yankee Stadium",
    "Pelham Bay Park", "Fordham Rd", "Kingsbridge Rd", "St George",
    "Tompkinsville", "Coney Island-Stillwell Av", "Prospect Park", "Euclid Av",
    "Sheepshead Bay", "Brighton Beach", "Roosevelt Island",
    "Astoria-Ditmars Blvd", "Dyckman St", "Marble Hill-225 St",
]

# Trunk route families. Stops are labelled by the family they sit on so the
# dashboard groups them the way riders think of the network, not by the
# individual services that happen to call at them.
LINE_FAMILIES = [
    ("1", "2", "3"),
    ("4", "5", "6"),
    ("7",),
    ("A", "C", "E"),
    ("B", "D", "F", "M"),
    ("G",),
    ("L",),
    ("N", "Q", "R", "W"),
    ("J", "Z"),
    ("SIR",),
]

FAMILY_ORDER = {"/".join(fam): i for i, fam in enumerate(LINE_FAMILIES)}

PEAK_START_HOUR = 7
PEAK_END_HOUR = 9
RIDERS_PER_TRAIN = 180
CAPACITY_ROUNDING = 50
CAP_FLOOR = 1200
CAP_CEILING = 24000


def _read_csv(path: str):
    with open(path, encoding="utf-8-sig", newline="") as fh:
        yield from csv.DictReader(fh)


def _gtfs_file(gtfs_dir: str, name: str) -> str:
    path = os.path.join(gtfs_dir, name)
    if not os.path.exists(path):
        raise FileNotFoundError(
            f"{name} not found in {gtfs_dir}. Download the subway GTFS from "
            "https://www.mta.info/developers/data (nyct/subway/google_transit.zip) "
            "and unzip it into a directory."
        )
    return path


def _parse_gtfs_times(value: str) -> int | None:
    """GTFS times are ``HH:MM:SS`` and may exceed 24h (e.g. ``25:10:00``)."""
    try:
        hours, minutes, _ = value.strip().split(":")
        return int(hours) * 60 + int(minutes)
    except (ValueError, AttributeError):
        return None


def _load_stops(gtfs_dir: str):
    """Index parent complexes by name and child stops by parent id."""
    parents_by_name: dict[str, list[dict]] = defaultdict(list)
    children_by_parent: dict[str, list[str]] = defaultdict(list)
    for row in _read_csv(_gtfs_file(gtfs_dir, "stops.txt")):
        if row.get("location_type") == "1":
            parents_by_name[row["stop_name"]].append(row)
        elif row.get("parent_station"):
            children_by_parent[row["parent_station"]].append(row["stop_id"])
    return parents_by_name, children_by_parent


def _load_trip_routes(gtfs_dir: str):
    """trip_id -> (route_short_name, route_color, runs_on_a_weekday)."""
    weekday_services = {
        row["service_id"]
        for row in _read_csv(_gtfs_file(gtfs_dir, "calendar.txt"))
        if row.get("monday") == "1"
    }
    # route_type 1 = subway, 2 = rail (the Staten Island Railway shares the feed
    # and two SIR stops are in the curated set).
    route_meta = {
        row["route_id"]: (row["route_short_name"], row.get("route_color", ""))
        for row in _read_csv(_gtfs_file(gtfs_dir, "routes.txt"))
        if row.get("route_type") in ("1", "2")
    }
    trips = {}
    for row in _read_csv(_gtfs_file(gtfs_dir, "trips.txt")):
        meta = route_meta.get(row["route_id"])
        if meta is None:
            continue
        trips[row["trip_id"]] = (meta[0], meta[1], row["service_id"] in weekday_services)
    return trips


def _scan_stop_times(gtfs_dir: str, wanted_children: set[str], trips: dict):
    """One pass over the 35 MB stop_times file.

    Returns ``(peak_arrivals, services)`` keyed by child stop id: peak arrival
    count during the weekday morning peak, and the set of route letters served
    (skipping ``*X`` rush-hour variants, e.g. ``<6X``, which are not trunk
    services).
    """
    peak_arrivals: dict[str, int] = defaultdict(int)
    services: dict[str, set[str]] = defaultdict(set)
    for row in _read_csv(_gtfs_file(gtfs_dir, "stop_times.txt")):
        stop_id = row["stop_id"]
        if stop_id not in wanted_children:
            continue
        trip = trips.get(row["trip_id"])
        if trip is None:
            continue
        route_short_name, _color, is_weekday = trip
        if not route_short_name.endswith("X"):
            services[stop_id].add(route_short_name)
        if not is_weekday:
            continue
        minute = _parse_gtfs_times(row.get("arrival_time", ""))
        if minute is None:
            continue
        if PEAK_START_HOUR * 60 <= minute < PEAK_END_HOUR * 60:
            peak_arrivals[stop_id] += 1
    return peak_arrivals, services


def _complex_stats(children: list[str], peak_arrivals: dict[str, int], services: dict[str, set[str]]):
    total = sum(peak_arrivals.get(c, 0) for c in children)
    # Arrivals are counted for both directions, so trains/hour is half of them.
    trains_per_hour = total / 2.0
    served = {s for c in children for s in services.get(c, ())}
    return trains_per_hour, served


def _family_for(served: set[str]) -> str:
    for family in LINE_FAMILIES:
        if served & set(family):
            return "/".join(family)
    return "/".join(sorted(served)) or "SIR"


def _capacity_for(trains_per_hour: float) -> int:
    raw = int(round(trains_per_hour * RIDERS_PER_TRAIN / CAPACITY_ROUNDING)) * CAPACITY_ROUNDING
    return min(CAP_CEILING, max(CAP_FLOOR, raw))


def build_stations(gtfs_dir: str, names: list[str] | None = None) -> list[dict]:
    """Extract curated MTA stations from an unzipped subway GTFS directory."""
    names = list(names or CURATED_STATIONS)
    parents_by_name, children_by_parent = _load_stops(gtfs_dir)

    missing = [n for n in names if n not in parents_by_name]
    if missing:
        raise ValueError(
            "GTFS feed does not contain these station names: " + ", ".join(missing)
        )

    selected = {n: parents_by_name[n] for n in names}
    wanted_children = {
        child
        for parents in selected.values()
        for parent in parents
        for child in children_by_parent.get(parent["stop_id"], ())
    }

    peak_arrivals, services = _scan_stop_times(gtfs_dir, wanted_children, _load_trip_routes(gtfs_dir))

    stations = []
    for name, parents in selected.items():
        def children_of(parent):
            return children_by_parent.get(parent["stop_id"], ())

        # Names such as "86 St" repeat across trunks; keep the complex whose
        # platforms carry the most peak service so the code matches the busiest
        # station of that name.
        best = max(
            parents,
            key=lambda p: sum(peak_arrivals.get(c, 0) for c in children_of(p)),
        )
        children = children_of(best)
        trains_per_hour, served = _complex_stats(children, peak_arrivals, services)
        stations.append({
            "code": best["stop_id"],
            "name": name,
            "line": _family_for(served),
            "capacity_per_hour": _capacity_for(trains_per_hour),
            "lat": round(float(best["stop_lat"]), 6),
            "lng": round(float(best["stop_lon"]), 6),
            "services": "/".join(sorted(served)),
            "trains_per_hour": round(trains_per_hour, 1),
        })

    stations.sort(key=lambda s: (FAMILY_ORDER.get(s["line"], 99), s["name"]))
    return stations


def station_frame(stations: list[dict]):
    import pandas as pd

    return pd.DataFrame(stations, columns=STATION_COLUMNS)


def write_stations(gtfs_dir: str, out_path: str, names: list[str] | None = None) -> list[dict]:
    stations = build_stations(gtfs_dir, names)
    frame = station_frame(stations)
    os.makedirs(os.path.dirname(os.path.abspath(out_path)), exist_ok=True)
    frame.to_csv(out_path, index=False)
    return stations


def parse(path: str, limit: int | None = None):
    """Importer-interface entry point.

    The GTFS feed carries no ridership counts (that is ``turnstile_*.txt`` /
    the mta importer), so this exposes only station identity. It returns empty
    detail frames shaped like the other importers for CLI compatibility.
    """
    stations = build_stations(path)
    if limit:
        stations = stations[:limit]
    name_by_code = {s["code"]: s["name"] for s in stations}
    line_by_code = {s["code"]: s["line"] for s in stations}
    import pandas as pd

    empty = pd.DataFrame(
        {
            "station_code": pd.Series(dtype=str),
            "timestamp": pd.Series(dtype="datetime64[ns]"),
            "entries": pd.Series(dtype=float),
            "exits": pd.Series(dtype=float),
        }
    )
    return empty, name_by_code, line_by_code


__all__ = [
    "CURATED_STATIONS",
    "LINE_FAMILIES",
    "STATION_COLUMNS",
    "build_stations",
    "station_frame",
    "write_stations",
    "parse",
]
