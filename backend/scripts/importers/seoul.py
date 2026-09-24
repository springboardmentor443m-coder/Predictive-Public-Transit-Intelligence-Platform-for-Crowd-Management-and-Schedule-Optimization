"""Seoul Metro ridership importer.

Targets the commonly published Seoul Metro card-swipe CSV (station × date ×
hour). Column names vary between English and Korean releases, so the parser
resolves them by alias. Daily-only totals are spread across the 24 hours using
the metro demand shape (documented approximation). Example shapes accepted:

    # hourly:
    #   station, date, hour, entries, exits
    #   Gangnam,  2024-01-05, 8, 1203, 998
    # daily (Korean):
    #   사용일자,   노선명,  역명,  승차총승객수, 하차총승객수
    #   2024-01-05, Line 2, 강남역, 4532, 3988
"""

import pandas as pd

from scripts.importers import base

STATION_ALIASES = ["station", "station_name", "역명", "역", "지하철역", "정류장명"]
TIME_ALIASES = ["timestamp", "time", "datetime", "일시", "시각", "조사일시"]
DATE_ALIASES = ["date", "일자", "사용일자", "기준일자"]
HOUR_ALIASES = ["hour", "시간", "h", "시"]
ENTRIES_ALIASES = ["entries", "entry", "승차", "승차승객", "승차총승객수", "board", "boardings", "in"]
EXITS_ALIASES = ["exits", "exit", "하차", "하차승객", "하차총승객수", "alight", "alightings", "out"]


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
    entries_col = _pick(df.columns, ENTRIES_ALIASES, "entries")
    exits_col = _pick(df.columns, EXITS_ALIASES, "exits")

    ts = None
    ts_col = next((c for c in TIME_ALIASES if c in df.columns), None)
    if ts_col is not None:
        ts = pd.to_datetime(df[ts_col], errors="coerce")
    else:
        date_col = _pick(df.columns, DATE_ALIASES, "date")
        date = pd.to_datetime(df[date_col], errors="coerce")
        hour_col = next((c for c in HOUR_ALIASES if c in df.columns), None)
        if hour_col is not None:
            ts = date + pd.to_timedelta(pd.to_numeric(df[hour_col], errors="coerce").fillna(0), unit="h")

    det = df[[station_col, entries_col, exits_col]].copy()
    det["station_code"] = _rank_codes(det[station_col])
    det["entries"] = pd.to_numeric(det[entries_col], errors="coerce").fillna(0.0)
    det["exits"] = pd.to_numeric(det[exits_col], errors="coerce").fillna(0.0)

    if ts is not None:
        det["timestamp"] = ts
        detail = det[["station_code", "timestamp", "entries", "exits"]].dropna(subset=["timestamp"])
    else:
        date_col = _pick(df.columns, DATE_ALIASES, "date")
        daily = det.assign(
            date=pd.to_datetime(df[date_col], errors="coerce"),
        ).dropna(subset=["date"])
        detail = base.expand_day_totals_to_hourly(
            daily,
            code_col="station_code",
            date_col="date",
            entries_col="entries",
            exits_col="exits",
        )

    detail = detail[detail["entries"] + detail["exits"] > 0]
    mapping = _mapping(detail, limit)
    detail["station_code"] = detail["station_code"].map(mapping)
    detail = detail.dropna(subset=["station_code"])
    detail["station_code"] = detail["station_code"].astype(str)
    name_by_code = {c: s for s, c in mapping.items()}
    return detail[["station_code", "timestamp", "entries", "exits"]], name_by_code, {}


def _rank_codes(station_series) -> pd.Series:
    return station_series.astype(str)


def _mapping(detail, limit=10):
    ranking = detail.groupby("station_code")["entries"].sum().sort_values(ascending=False)
    return {s: f"ST{i + 1:02d}" for i, s in enumerate(ranking.index.tolist()[:limit])}