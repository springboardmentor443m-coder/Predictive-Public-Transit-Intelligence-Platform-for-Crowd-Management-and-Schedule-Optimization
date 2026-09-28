"""CLI to import a real transit dataset into the demo pipeline.

Writes ``ridership_hourly.csv`` and ``stations.csv`` (re-anchored to *now*)
into ``--output-dir`` (default ``backend/data``), ready for
``python scripts/seed_db.py --refresh``.
"""

import argparse
import os
import sys

_BACKEND_DIR = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
sys.path.insert(0, _BACKEND_DIR)

from scripts.importers import base, mta, mta_gtfs, seoul, tfl  # noqa: E402

IMPORTERS = {
    "mta": mta,
    "mta-gtfs": mta_gtfs,
    "seoul": seoul,
    "tfl": tfl,
}

# Station-identity-only importers: they rewrite stations.csv from a transit
# authority's own network file and carry no ridership counts.
STATION_ONLY = {"mta-gtfs"}


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--city", choices=sorted(IMPORTERS), required=True)
    parser.add_argument(
        "--input",
        required=True,
        help="Path to the real dataset CSV (or, for mta-gtfs, the unzipped GTFS directory)",
    )
    parser.add_argument(
        "--output-dir",
        default=os.path.join(_BACKEND_DIR, "data"),
        help="Where to write ridership_hourly.csv + stations.csv",
    )
    parser.add_argument("--prefix", default="", help="Optional filename prefix (for testing, e.g. 'test_')")
    parser.add_argument("--limit", type=int, default=10, help="Max stations to keep (top N by volume)")
    args = parser.parse_args()

    if args.city in STATION_ONLY:
        _run_station_only(args)
        return

    importer = IMPORTERS[args.city]
    print(f"[import] {args.city} <- {args.input}")
    detail, name_by_code, line_by_code = importer.parse(args.input, limit=args.limit)

    # Re-anchor to "now" *before* aggregation so the derived hour/weekday
    # columns stay consistent with the shifted timestamps the seed consumes.
    detail["timestamp"] = base.recenter_to_now(detail["timestamp"])

    ridership = base.hourly_frame(
        detail,
        code_col="station_code",
        ts_col="timestamp",
        entries_col="entries",
        exits_col="exits",
        name_by_code=name_by_code,
        line_by_code=line_by_code,
    )

    caps = {
        c: base.default_capacity(g["entries"])
        for c, g in ridership.groupby("station_code")
    }
    names = {
        c: g["station_name"].iloc[0]
        for c, g in ridership.groupby("station_code")
    }
    stations = base.station_frame(names, caps, line_by_code)
    names.update({c: n for c, n in name_by_code.items() if c not in names})
    ridership["station_name"] = ridership["station_code"].map(names)
    ridership["line"] = ridership["station_code"].map(
        {c: l for c, l in line_by_code.items() if l}
    ).fillna("Imported")

    base.write_outputs(ridership, stations, args.output_dir, prefix=args.prefix)
    window = ridership["timestamp"].max()
    print(f"[ok] newest row re-anchored to {window} "
          f"(seed freshness requires <= 3 days from now)")
    print(f"[ok] {ridership['station_code'].nunique()} stations "
          f"({len(ridership)} station-hours)")


def _run_station_only(args: argparse.Namespace) -> None:
    """Station-only importers rewrite stations.csv from the agency network file."""
    os.makedirs(args.output_dir, exist_ok=True)
    out_path = os.path.join(args.output_dir, f"{args.prefix}stations.csv")
    print(f"[import] {args.city} <- {args.input}")
    stations = mta_gtfs.write_stations(args.input, out_path)
    print(f"[out] {out_path}  ({len(stations)} stations)")
    for line in sorted({s["line"] for s in stations}):
        count = sum(1 for s in stations if s["line"] == line)
        print(f"  {line:>8}  {count:>2} stations")
    caps = [s["capacity_per_hour"] for s in stations]
    print(f"[ok] capacity range {min(caps)}-{max(caps)} riders/hour")
    print("[ok] next: python scripts/seed_db.py --refresh")


if __name__ == "__main__":
    main()