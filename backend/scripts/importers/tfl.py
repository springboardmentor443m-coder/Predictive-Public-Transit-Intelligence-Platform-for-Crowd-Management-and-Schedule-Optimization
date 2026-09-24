"""Transport for London Entry & Exit counts importer.

The published TfL dataset lists annual entrances/exits per Underground
station, e.g.::

    Year, Station, Entrances, Exits
    2015, Waterloo,        ...,     ...

The importer expands each station-year total across the year's days and hours
using the metro demand shape (see ``base.expand_year_to_hourly``). The busiest
stations map onto the demo scheme (ST01..ST10).
"""

import pandas as pd

from scripts.importers import base

STATION_ALIASES = ["station", "station_name", "stn"]
YEAR_ALIASES = ["year", "연도"]
ENTRIES_ALIASES = ["entries", "entrances", "entry", "entry_count", "entrances_estim"]
EXITS_ALIASES = ["exits", "exit", "exit_count", "exits_estim"]


def _pick(columns, aliases, label):
    for alias in aliases:
        exact = [c for c in columns if c.strip().lower() == alias.lower()]
        if exact:
            return exact[0]
        fuzzy = [c for c in columns if alias.lower() in c.strip().lower()]
        if fuzzy:
            return fuzzy[0]
    raise ValueError(
        f"Could not find a {label} column in {list(columns)} (aliases: {aliases})"
    )


def parse(path: str, limit: int = 10):
    df = base.read_csv(path)
    df = df.rename(columns={c: c.strip() for c in df.columns})
    station_col = _pick(df.columns, STATION_ALIASES, "station")
    year_col = _pick(df.columns, YEAR_ALIASES, "year")
    entries_col = _pick(df.columns, ENTRIES_ALIASES, "entrances")
    exits_col = _pick(df.columns, EXITS_ALIASES, "exits")

    det = df[[station_col, year_col, entries_col, exits_col]].rename(columns={
        station_col: "station", year_col: "year",
        entries_col: "entries", exits_col: "exits",
    })
    det["year"] = pd.to_numeric(det["year"], errors="coerce")
    det = det.dropna(subset=["year"])
    det["entries"] = pd.to_numeric(det["entries"], errors="coerce").fillna(0.0)
    det["exits"] = pd.to_numeric(det["exits"], errors="coerce").fillna(0.0)
    det = det[det["entries"] + det["exits"] > 0]

    expanded = base.expand_year_to_hourly(
        det,
        code_col="station",
        year_col="year",
        entries_col="entries",
        exits_col="exits",
    )
    mapping = _mapping(expanded, limit)
    expanded["station_code"] = expanded["station_code"].map(mapping)
    expanded = expanded.dropna(subset=["station_code"])
    expanded = expanded[expanded["entries"] + expanded["exits"] > 0]
    name_by_code = {c: s for s, c in mapping.items()}
    return expanded[["station_code", "timestamp", "entries", "exits"]], name_by_code, {}


def _mapping(detail, limit=10):
    ranking = detail.groupby("station_code")["entries"].sum().sort_values(ascending=False)
    return {s: f"ST{i + 1:02d}" for i, s in enumerate(ranking.index.tolist()[:limit])}