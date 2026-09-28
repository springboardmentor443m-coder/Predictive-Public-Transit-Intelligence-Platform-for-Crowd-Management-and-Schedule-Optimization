"""Build the complete NYC rail network geometry, once, from the official MTA GTFS.

While build_connections.py keeps only edges between monitored stations, this
script snapshots the WHOLE subway: every station-level stop and every rail
segment (two stations consecutive on the same train run). The frontend's
geographic view uses it as the real-world base map, then overlays the monitored
59 stations with live congestion — so no line is every "missing" and the map
reads like the actual network.

Output: data/nyc_network.json

    {
      "stations": [{ "c": code, "n": name, "lat": ..., "lng": ... }, ...],
      "segments": [{ "a": code, "b": code, "r": "1;2;3" }, ...],
      "monitored": [code, ...]   // in data/stations.csv order
    }

`a`/`b` always reference station codes from `stations`; the frontend looks up
the coordinates so the payload stays small. Segments are deduplicated
undirected pairs with the semicolon-joined total of route short names that use
them (runs both directions collapse into one entry).

Usage:
    python scripts/build_network.py --gtfs-dir <extracted gtfs dir> [--out data/nyc_network.json]
"""

import argparse
import json
import os
from collections import defaultdict

import pandas as pd

DATA_DIR = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "data")


def build_network(gtfs_dir: str, monitored_codes: list[str]) -> dict:
    stops = pd.read_csv(os.path.join(gtfs_dir, "stops.txt"), dtype={"stop_id": str})

    # Station-level stops are the ones without a parent (platforms carry the
    # parent_station reference). Normalise stop ids so stop_times pairs land on
    # their parent junctions.
    parent: dict[str, str] = {}
    for s in stops.itertuples(index=False):
        ps = s.parent_station
        if pd.isna(ps) or str(ps) == "" or str(ps) == "nan":
            parent[str(s.stop_id)] = str(s.stop_id)
        else:
            parent[str(s.stop_id)] = str(ps)

    station_info: dict[str, dict] = {}
    for s in stops.itertuples(index=False):
        ps = s.parent_station
        is_station = pd.isna(ps) or str(ps) == "" or str(ps) == "nan"
        if not is_station:
            continue
        code = str(s.stop_id)
        name = str(s.stop_name) if not pd.isna(s.stop_name) else code
        station_info[code] = {
            "c": code,
            "n": name,
            "lat": round(float(s.stop_lat), 6),
            "lng": round(float(s.stop_lon), 6),
        }

    def station_of(sid: str) -> str:
        return parent.get(sid, sid)

    routes = pd.read_csv(
        os.path.join(gtfs_dir, "routes.txt"),
        dtype={"route_id": str, "route_short_name": str},
    )[["route_id", "route_short_name"]].drop_duplicates()
    route_name = {k: v for k, v in zip(routes["route_id"], routes["route_short_name"]) if not pd.isna(v)}

    trips = pd.read_csv(
        os.path.join(gtfs_dir, "trips.txt"),
        usecols=["trip_id", "route_id"],
        dtype=str,
    ).drop_duplicates()
    trip_route = dict(zip(trips["trip_id"], trips["route_id"]))

    stop_times = pd.read_csv(
        os.path.join(gtfs_dir, "stop_times.txt"),
        usecols=["trip_id", "stop_id", "stop_sequence"],
        dtype={"trip_id": str, "stop_id": str, "stop_sequence": int},
    )
    stop_times["station"] = stop_times["stop_id"].map(station_of)
    stop_times = stop_times[stop_times["station"].isin(station_info)]

    segment_routes: dict[frozenset, set[str]] = defaultdict(set)
    for trip_id, frame in stop_times.groupby("trip_id", sort=False):
        route_id = trip_route.get(trip_id)
        name = route_name.get(route_id) if route_id else None
        if name is None:
            continue
        seen = frame.sort_values("stop_sequence")["station"].dropna().tolist()
        for a, b in zip(seen, seen[1:]):
            if a == b:
                continue
            segment_routes[frozenset((a, b))].add(str(name))

    monitored = [dict(s) for s in station_info.values() if s["c"] in set(monitored_codes)]

    return {
        "stations": sorted(station_info.values(), key=lambda s: (s["lng"], -s["lat"])),
        "segments": [
            {"a": a, "b": b, "r": ";".join(sorted(routes_set))}
            for a, b, routes_set in sorted(
                (min(pair), max(pair), rs) for pair, rs in segment_routes.items()
            )
            if a in station_info and b in station_info
        ],
        "monitored": monitored_codes,
    }


def main() -> None:
    parser = argparse.ArgumentParser(description="Snapshot the full MTA network from GTFS.")
    parser.add_argument("--gtfs-dir", required=True, help="Extracted MTA google_transit.zip directory")
    parser.add_argument("--out", default=os.path.join(DATA_DIR, "nyc_network.json"))
    args = parser.parse_args()

    df = pd.read_csv(os.path.join(DATA_DIR, "stations.csv"), dtype={"code": str})
    monitored_codes = df["code"].astype(str).tolist()

    network = build_network(args.gtfs_dir, monitored_codes)
    with open(args.out, "w", encoding="utf-8") as fh:
        json.dump(network, fh, ensure_ascii=False, separators=(",", ":"))

    monitored_in_feed = {s["c"] for s in network["stations"]}
    missing = [c for c in monitored_codes if c not in monitored_in_feed]
    total_segments = len(network["segments"])
    monitored_set = set(monitored_codes)
    linked = sum(1 for s in network["segments"] if s["a"] in monitored_set and s["b"] in monitored_set)

    print(f"network stations: {len(network['stations'])}")
    print(f"segments:         {total_segments} ({linked} with both ends monitored)")
    print(f"monitored:        {len(network['monitored'])} ({len(network['monitored']) - len(missing)} matched the feed)")
    if missing:
        print("WARNING: not in the feed:", missing)
    print(f"wrote {os.path.abspath(args.out)}")


if __name__ == "__main__":
    main()