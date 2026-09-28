"""Build the real MetroFlow station connection graph from the official MTA GTFS.

`data/stations.csv` carries the subway's canonical station codes (L08, R01,
A41, 128, ...), which are exactly the station-level stop_ids of the GTFS feed.
This script walks the feed's trips (consecutive stops on the same run are the
rail adjacency) and its transfers table (walking/timed interchanges), keeps only
edges whose endpoints are in `data/stations.csv`, and writes
`data/connections.csv`:

    from_code,to_code,kind,vias

    kind:
      along_line - stations consecutive on the same train run (also covers
                   same-station trunk interchanges while staying "on the line")
      transfer   - a separate walking/rapid interchange between two stations

    vias        - semicolon-joined trunk service labels (1, L, N/Q/R/W, ...)

The result is the ground truth for "which junction connects to which": the
frontend renders these edges on the metro map and the station detail panel
derives its "Connects to" list from them.

Usage:
    python scripts/build_connections.py --gtfs-dir <extracted gtfs dir>
"""

import argparse
import os
import sys
from collections import defaultdict

import pandas as pd

DATA_DIR = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "data")


def our_station_codes() -> set[str]:
    df = pd.read_csv(os.path.join(DATA_DIR, "stations.csv"), dtype={"code": str})
    return set(df["code"].astype(str))


def build_edges(gtfs_dir: str, ours: set[str]) -> list[dict]:
    stops = pd.read_csv(os.path.join(gtfs_dir, "stops.txt"), dtype={"stop_id": str})

    # MTA stop_times reference *platform* stop ids (120N) while stations.csv uses
    # the parent station ids (120). Normalise every stop id through the
    # parent_station map so the feed's consecutive-stop pairs land on junctions.
    parent: dict[str, str] = {}
    for s in stops.itertuples(index=False):
        ps = s.parent_station
        if pd.isna(ps) or str(ps) == "" or str(ps) == "nan":
            parent[str(s.stop_id)] = str(s.stop_id)
        else:
            parent[str(s.stop_id)] = str(ps)
    station_ids = set(parent.values())

    def station_of(sid: str) -> str:
        return parent.get(sid, sid)

    routes = pd.read_csv(
        os.path.join(gtfs_dir, "routes.txt"),
        dtype={"route_id": str, "route_short_name": str},
    )[["route_id", "route_short_name"]].drop_duplicates()
    route_name = dict(zip(routes["route_id"], routes["route_short_name"]))
    route_name = {k: v for k, v in route_name.items() if pd.notna(v)}

    # route per trip
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

    along: dict[frozenset, set[str]] = defaultdict(set)
    for trip_id, frame in stop_times.groupby("trip_id", sort=False):
        route_id = trip_route.get(trip_id)
        name = route_name.get(route_id) if route_id else None
        if name is None:
            continue
        seen = frame.sort_values("stop_sequence")["station"].dropna().tolist()
        for a, b in zip(seen, seen[1:]):
            if a in ours and b in ours and a in station_ids and b in station_ids:
                along[frozenset((a, b))].add(str(name))

    transfers = pd.read_csv(
        os.path.join(gtfs_dir, "transfers.txt"),
        dtype={"from_stop_id": str, "to_stop_id": str},
    )
    transfer_edges = set()
    for row in transfers.itertuples(index=False):
        a, b = station_of(str(row.from_stop_id)), station_of(str(row.to_stop_id))
        if a in ours and b in ours and a != b and a in station_ids and b in station_ids:
            transfer_edges.add(frozenset((a, b)))

    # Feed corrections. GTFS is authoritative but not complete for interchanges
    # at the same physical complex, and occasionally lists a bogus one.
    PHANTOM_TRANSFERS = {
        # Queensboro Plaza (7) <-> 34 St-Herald Sq (N/Q/R/W): ~6km apart in the
        # feed; rides on two 0-min entries are a data artefact.
        frozenset(("718", "R09")),
    }
    SAME_COMPLEX_TRANSFERS = {
        # Queensboro Plaza: 7 and N/W share the same island concourse (instant
        # cross-platform). The feed omits it as a walking transfer.
        frozenset(("718", "R05")),
        # Times Sq-42 St (1/2/3) and Grand Central-42 St (4/5/6): the 42 St
        # Shuttle and the underground passage link the two complexes. The feed
        # models the shuttle as its own stops (901/902), so the interchange is
        # invisible unless added here.
        frozenset(("127", "631")),
    }
    transfer_edges = (transfer_edges - PHANTOM_TRANSFERS) | SAME_COMPLEX_TRANSFERS

    rows: list[dict] = []
    for pair, vias in sorted(along.items(), key=lambda kv: (min(kv[0]), max(kv[0]))):
        a, b = tuple(pair)
        # The S shuttle services (FS/GS/H) are real rail edges; keep their label
        # so the map can colour and describe them accurately.
        rows.append({
            "from_code": min(a, b),
            "to_code": max(a, b),
            "kind": "along_line",
            "vias": ";".join(sorted(v for v in vias if v)) or "transfer",
        })
    for a, b in sorted(transfer_edges, key=lambda p: (min(p), max(p))):
        a, b = min(a, b), max(a, b)
        if frozenset((a, b)) in along:
            continue  # walking transfer at a stop already linked by rail
        rows.append({"from_code": a, "to_code": b, "kind": "transfer", "vias": "transfer"})
    return rows


def validate(rows: list[dict], ours: set[str]) -> None:
    endpoints = {r["from_code"] for r in rows} | {r["to_code"] for r in rows}
    isolated = sorted(ours - endpoints)
    if isolated:
        print(f"WARNING: {len(isolated)} stations have NO connections: {isolated}")

    adj: dict[str, set[str]] = defaultdict(set)
    for r in rows:
        adj[r["from_code"]].add(r["to_code"])
        adj[r["to_code"]].add(r["from_code"])

    # Connectivity: the subway is a single network, so every station must be in
    # one connected component.
    if ours:
        start = next(iter(ours))
        seen = set()
        stack = [start]
        while stack:
            n = stack.pop()
            if n in seen:
                continue
            seen.add(n)
            stack.extend(adj[n] - seen)
        if seen != ours:
            missing = sorted(ours - seen)
            print(f"WARNING: graph is not connected; unreachable: {missing}")

    degree = {s: len(adj[s]) for s in ours}
    hubs = sorted(degree, key=degree.get, reverse=True)[:8]
    print("Busiest junctions (by connections):")
    for h in hubs:
        print(f"  {h:>6}  degree={degree[h]}")


def main() -> None:
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--gtfs-dir", required=True, help="directory of extracted MTA subway GTFS text files")
    args = ap.parse_args()

    ours = our_station_codes()
    print(f"{len(ours)} stations monitored; building edges from {args.gtfs_dir} ...")
    rows = build_edges(args.gtfs_dir, ours)
    validate(rows, ours)

    out = os.path.join(DATA_DIR, "connections.csv")
    pd.DataFrame(rows, columns=["from_code", "to_code", "kind", "vias"]).to_csv(out, index=False)
    print(f"Wrote {len(rows)} connections -> {out}")


if __name__ == "__main__":
    main()