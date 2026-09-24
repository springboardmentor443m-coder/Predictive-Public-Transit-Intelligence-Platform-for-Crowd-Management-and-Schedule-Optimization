"""MTA turnstile data importer.

Parses the real NYC open-data turnstile format (the weekly ``turnstile_*.txt``
files). Each row is a cumulative audit point::

    C/A,UNIT,SCP,STATION,LINENAME,DIVISION,DATE,TIME,DESC,ENTRIES,EXITS
    A002,R051,02-00-00,59 ST,1,IRT,05/15/2024,00:00:00,REGULAR,1234567,7654321

ENTRIES/EXITS are running counters per tap device (C/A-UNIT-SCP); DESC splits
REGULAR audits from RECOVR_AUD. The importer diffs consecutive audits and sums
both DESC variants, producing real per-hour station traffic. The top stations
by volume map onto the demo scheme (ST01..ST10) used by the seed pipeline.
"""

import pandas as pd

from scripts.importers import base

LIMIT_STATIONS = 10

DEVICE_COLS = ["C/A", "UNIT", "SCP"]


def parse(path: str, limit: int = LIMIT_STATIONS):
    entries = base.read_csv(path, dtype=str)
    needed = DEVICE_COLS + ["STATION", "LINENAME", "DATE", "TIME", "DESC", "ENTRIES", "EXITS"]
    missing = [c for c in needed if c not in entries.columns]
    if missing:
        raise ValueError(
            "Unrecognized MTA turnstile format: missing columns "
            + ", ".join(missing)
            + " (expected the MTA turnstile_*.txt schema: "
            + ", ".join(needed)
            + ")"
        )
    df = entries.copy()
    df["timestamp"] = pd.to_datetime(df["DATE"].str.strip() + " " + df["TIME"].str.strip())
    df = df.sort_values(DEVICE_COLS + ["timestamp"]).reset_index(drop=True)

    diffs = []
    for key, g in df.groupby(DEVICE_COLS, sort=False):
        g = g.sort_values("timestamp")
        d_ent = g["ENTRIES"].astype(float).diff().fillna(0.0).clip(lower=0)
        d_ext = g["EXITS"].astype(float).diff().fillna(0.0).clip(lower=0)
        diffs.append(pd.DataFrame({
            "station": g["STATION"].astype(str).str.upper(),
            "line": g["LINENAME"].fillna("").str.split(",").str[0],
            "timestamp": g["timestamp"],
            "entries": d_ent,
            "exits": d_ext,
        }))
    detail = pd.concat(diffs, ignore_index=True)
    detail = detail[detail["entries"] + detail["exits"] > 0]

    ranking = detail.groupby("station")["entries"].sum().sort_values(ascending=False)
    top = ranking.head(limit).index.tolist()
    code_of = {s: f"ST{i + 1:02d}" for i, s in enumerate(top)}
    detail["station_code"] = detail["station"].map(code_of).fillna("")
    detail = detail[detail["station_code"] != ""].copy()

    name_by_code = {code: s for s, code in code_of.items()}
    line_by_code = {
        code: detail[detail["station_code"] == code]["line"].mode().iat[0]
        for code in code_of.values()
    }
    return detail[["station_code", "timestamp", "entries", "exits"]], name_by_code, line_by_code