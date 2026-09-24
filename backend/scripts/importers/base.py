"""Shared normalization for external transit-dataset importers.

Each importer (mta / seoul / tfl) parses its real-world CSV into a common
long "detail" frame — station id, timestamp, entries, exits — and calls
``hourly_frame`` to build the exact schema that ``scripts/seed_db.py`` and
``scripts/generate_data.py`` produce, re-anchored so the newest observation
lands on *now* (the seed pipeline only accepts a CSV fresher than 3 days).
"""

import os

import numpy as np
import pandas as pd

from app.ml import features as feat

RIDERSHIP_COLUMNS = [
    "station_code", "station_name", "line", "timestamp", "hour", "weekday",
    "is_weekend", "is_peak", "entries", "exits", "occupancy", "capacity",
    "occupancy_pct", "congestion_level",
]

STATION_COLUMNS = ["code", "name", "line", "capacity_per_hour"]


def read_csv(path: str, **kwargs) -> pd.DataFrame:
    """Read a transitive CSV with encoding fallbacks (exports from the transit
    agencies are commonly utf-8-sig (BOM), cp949 for Korean files, or legacy
    ANSI)."""
    last = None
    for enc in ("utf-8-sig", "utf-8", "cp949", "cp1252"):
        try:
            return pd.read_csv(path, encoding=enc, **kwargs)
        except (UnicodeDecodeError, UnicodeError) as e:
            last = e
    raise last

DEFAULT_CAPACITY = 520.0
CAP_FLOOR = 400.0
CAP_CEILING = 20000.0
HISTORY_DAYS = 7


def congestion_level(occ_pct: float) -> str:
    if occ_pct >= 0.90:
        return "critical"
    if occ_pct >= 0.75:
        return "high"
    if occ_pct >= 0.55:
        return "medium"
    return "low"


def recenter_to_now(ts: pd.Series) -> pd.Series:
    """Shift a timestamp series so its maximum lands on the current hour,
    preserving hour alignment (the seed freshness check requires a CSV whose
    newest row is `<= 3 days` old)."""
    ts = pd.to_datetime(ts)
    newest = ts.max()
    now_floor = pd.Timestamp.now(tz="UTC").tz_localize(None).floor("h")
    offset = now_floor - newest
    return ts + offset


def default_capacity(hourly_entries: pd.Series) -> float:
    """Capacity estimate from observed traffic when the dataset does not
    carry one: the 99th-percentile hourly flow scaled up to a per-hour
    station capacity and clamped to a sane range."""
    if hourly_entries is None or len(hourly_entries) == 0:
        return DEFAULT_CAPACITY
    p99 = float(np.percentile(np.asarray(hourly_entries, dtype=float), 99))
    return float(np.clip(p99 * 4.0, CAP_FLOOR, CAP_CEILING))


def hourly_frame(
    detail: pd.DataFrame,
    *,
    code_col: str,
    ts_col: str,
    entries_col: str,
    exits_col: str,
    name_by_code: dict[str, str],
    line_by_code: dict[str, str] | None = None,
    cap_by_code: dict[str, float] | None = None,
) -> pd.DataFrame:
    """Aggregate per-station-hour rows into the ridership_hourly.csv schema.

    ``entries``/``exits`` are summed per station+hour; occupancy fractions are
    derived the same way ``scripts/generate_data.py`` does so the ML features,
    congestion buckets and the seed pipeline see a familiar distribution.
    """
    df = detail.copy()
    df[ts_col] = pd.to_datetime(df[ts_col])
    df[entries_col] = df[entries_col].clip(lower=0)
    df[exits_col] = df[exits_col].clip(lower=0)

    hourly = (
        df.groupby(
            [code_col, pd.Grouper(key=ts_col, freq="h")],
            as_index=False,
        )
        .agg(entries=(entries_col, "sum"), exits=(exits_col, "sum"))
        .rename(columns={code_col: "station_code", ts_col: "timestamp"})
    )
    hourly["station_code"] = hourly["station_code"].astype(str)

    hourly["station_name"] = hourly["station_code"].map(name_by_code).fillna("Unknown")
    hourly["line"] = hourly["station_code"].map(line_by_code or {}).fillna("Imported")
    counts = hourly.groupby("station_code")["entries"]
    hourly["capacity"] = hourly["station_code"].map(
        {c: default_capacity(g) for c, g in (cap_by_code or counts)}
    )
    # Reference generate_data.py semantics: entries ~= capacity * pct / 4, so a
    # peak-hour entry level maps to ~100% occupancy.
    hourly["occupancy_pct"] = np.clip(4.0 * hourly["entries"] / hourly["capacity"], 0.02, 1.15)
    hourly["occupancy"] = hourly["entries"].round().astype(int)
    hourly["occupancy_pct"] = (hourly["occupancy_pct"] * 100.0).round(2)

    hourly["hour"] = hourly["timestamp"].dt.hour.astype(int)
    hourly["weekday"] = hourly["timestamp"].dt.weekday.astype(int)
    hourly["is_weekend"] = (hourly["weekday"] >= 5).astype(int)
    hourly["is_peak"] = hourly["hour"].isin(feat.PEAK_MULTIPLIER).astype(int)
    hourly["congestion_level"] = (hourly["occupancy_pct"] / 100.0).map(congestion_level)

    hourly["capacity"] = hourly["capacity"].astype(int)
    return hourly[RIDERSHIP_COLUMNS].sort_values(["station_code", "timestamp"]).reset_index(drop=True)


def expand_year_to_hourly(
    detail: pd.DataFrame,
    *,
    code_col: str,
    year_col: str,
    entries_col: str,
    exits_col: str,
) -> pd.DataFrame:
    """Expand annual per-station totals (TfL Entry & Exit counts) into a
    station-hour detail frame using the metro demand shape: year totals are
    split across days (weekday vs weekend split) and then across the 24 hours
    of each day with the baseline occupancy profile normalized to sum to 1."""
    rows = []
    rng = np.random.default_rng(42)
    for _, r in detail.iterrows():
        code = str(r[code_col])
        year = int(r[year_col])
        total_e = float(r[entries_col])
        total_x = float(r[exits_col])
        start = pd.Timestamp(year=year, month=1, day=1)
        end = min(start + pd.offsets.YearEnd(0), pd.Timestamp(year=year, month=12, day=31))
        days = pd.date_range(start, end)
        n_days = len(days)
        profile = np.array([feat.BASELINE_OCCUPANCY[h] for h in range(24)], dtype=float)
        for d in days:
            # Day shape: baseline curve, softened on weekends, then normalized
            # so each day contributes exactly 1/n_days of the annual total.
            hw = profile * (feat.WEEKEND_FACTOR if d.weekday() >= 5 else 1.0)
            hw = hw / hw.sum()
            for h, hw_hour in enumerate(hw):
                share = hw_hour / n_days
                rows.append({
                    "station_code": code,
                    "timestamp": d + pd.Timedelta(hours=h) + pd.Timedelta(
                        minutes=int(rng.integers(0, 60))),
                    "entries": total_e * share,
                    "exits": total_x * share,
                })
    return pd.DataFrame(rows)


def expand_day_totals_to_hourly(
    detail: pd.DataFrame,
    *,
    code_col: str,
    date_col: str,
    entries_col: str,
    exits_col: str,
) -> pd.DataFrame:
    """Spread daily per-station totals across the hours of each day using the
    metro demand shape (weekday vs weekend handled), so daily datasets still
    feed the hourly seed pipeline."""
    daily = detail.copy()
    daily[date_col] = pd.to_datetime(daily[date_col])
    daily[entries_col] = pd.to_numeric(daily[entries_col], errors="coerce").fillna(0.0)
    daily[exits_col] = pd.to_numeric(daily[exits_col], errors="coerce").fillna(0.0)
    rows = []
    profile = np.array([feat.BASELINE_OCCUPANCY[h] for h in range(24)], dtype=float)
    for _, r in daily.iterrows():
        hw = profile * (feat.WEEKEND_FACTOR if r[date_col].weekday() >= 5 else 1.0)
        hw = hw / hw.sum()
        for h, share in enumerate(hw):
            rows.append({
                "station_code": str(r[code_col]),
                "timestamp": r[date_col] + pd.Timedelta(hours=h),
                "entries": r[entries_col] * share,
                "exits": r[exits_col] * share,
            })
    return pd.DataFrame(rows)


def write_outputs(ridership: pd.DataFrame, stations: pd.DataFrame, out_dir: str, prefix: str = "") -> None:
    os.makedirs(out_dir, exist_ok=True)
    rp = os.path.join(out_dir, f"{prefix}ridership_hourly.csv")
    sp = os.path.join(out_dir, f"{prefix}stations.csv")
    ridership.to_csv(rp, index=False)
    stations[STATION_COLUMNS].to_csv(sp, index=False)
    print(f"[out] {rp}  ({len(ridership)} rows)")
    print(f"[out] {sp}")


def station_frame(
    name_by_code: dict[str, str],
    cap_by_code: dict[str, float],
    line_by_code: dict[str, str] | None = None,
) -> pd.DataFrame:
    return pd.DataFrame([{
        "code": code,
        "name": name,
        "line": (line_by_code or {}).get(code, "Imported"),
        "capacity_per_hour": int(round(cap_by_code.get(code, DEFAULT_CAPACITY))),
    } for code, name in sorted(name_by_code.items())])