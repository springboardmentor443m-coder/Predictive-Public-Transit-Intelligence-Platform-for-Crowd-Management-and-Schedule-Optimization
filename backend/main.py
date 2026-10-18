from __future__ import annotations
from pathlib import Path
from datetime import datetime, timezone
from threading import Lock
import math
import pandas as pd
import numpy as np
from fastapi import FastAPI, HTTPException, Query
from fastapi.responses import HTMLResponse, StreamingResponse
from fastapi.staticfiles import StaticFiles
from pydantic import BaseModel, Field

ROOT = Path(__file__).resolve().parents[1]
DATA_DIR = ROOT / "data"
FRONTEND = ROOT / "frontend"
DATA_FILE = DATA_DIR / "seoul-metro-2015.logs.csv.gz"
CSV_FILE = DATA_DIR / "seoul-metro-2015.logs.csv"
REQUIRED = ["timestamp", "station_code", "people_in", "people_out"]
# Keep the dashboard responsive by analysing a consistent, deterministic subset.
SELECTED_STATION_LIMIT = 20
_cache = None
_cache_lock = Lock()
_sim_index = 0
_announcements = []

app = FastAPI(title="MetroFlow Seoul API", version="1.0.0", description="Historical-data-powered public transit crowd intelligence demo.")
app.mount("/static", StaticFiles(directory=FRONTEND / "static"), name="static")


def load_data() -> pd.DataFrame:
    global _cache
    with _cache_lock:
        if _cache is not None:
            return _cache
        source = CSV_FILE if CSV_FILE.exists() else DATA_FILE
        if not source.exists():
            raise HTTPException(status_code=503, detail="Dataset not found. Place seoul-metro-2015.logs.csv or seoul-metro-2015.logs.csv.gz in the data folder.")
        try:
            # Read only the four required fields. First identify a stable set of 20
            # station codes, then discard all other rows before expensive date parsing
            # and aggregation. The original dataset remains unchanged on disk.
            df = pd.read_csv(source, compression="infer", usecols=lambda c: c in REQUIRED)
            missing = [c for c in REQUIRED if c not in df.columns]
            if missing:
                raise HTTPException(status_code=500, detail=f"Dataset is missing required columns: {', '.join(missing)}")
            df = df[REQUIRED].copy()
            df["station_code"] = pd.to_numeric(df["station_code"], errors="coerce")
            available_codes = sorted(df["station_code"].dropna().astype(int).unique().tolist())
            selected_codes = set(available_codes[:SELECTED_STATION_LIMIT])
            df = df[df["station_code"].isin(selected_codes)].copy()
            df["timestamp"] = pd.to_datetime(df["timestamp"], errors="coerce", utc=True)
            for c in ["people_in", "people_out"]:
                df[c] = pd.to_numeric(df[c], errors="coerce")
            df = df.dropna(subset=REQUIRED).copy()
            df["station_code"] = df["station_code"].astype(int)
            df["people_in"] = df["people_in"].clip(lower=0).astype(int)
            df["people_out"] = df["people_out"].clip(lower=0).astype(int)
            # Keep source timestamps in UTC internally; display as Asia/Seoul.
            df["total_flow"] = df["people_in"] + df["people_out"]
            df["local_time"] = df["timestamp"].dt.tz_convert("Asia/Seoul")
            df["hour"] = df["local_time"].dt.hour
            df["date"] = df["local_time"].dt.strftime("%Y-%m-%d")
            _cache = df.sort_values("timestamp").reset_index(drop=True)
            return _cache
        except HTTPException:
            raise
        except Exception as e:
            raise HTTPException(status_code=500, detail=f"Could not read dataset: {e}")


def safe_num(value):
    if pd.isna(value) or not np.isfinite(value): return 0
    return int(value) if float(value).is_integer() else round(float(value), 2)


def filtered_station(station_code: int | None = None) -> pd.DataFrame:
    df = load_data()
    if station_code is not None:
        subset = df[df.station_code == station_code]
        if subset.empty:
            raise HTTPException(status_code=404, detail=f"Station code {station_code} was not found.")
        return subset
    return df


def make_alerts(df: pd.DataFrame, limit: int = 20):
    # Data-derived thresholds are descriptive demo thresholds, not official capacity limits.
    q95 = float(df.total_flow.quantile(.95)) if len(df) else 0
    q995 = float(df.total_flow.quantile(.995)) if len(df) else 0
    tail = df.nlargest(limit, "total_flow")
    alerts = []
    for _, r in tail.iterrows():
        flow = int(r.total_flow)
        severity = "Critical" if flow >= q995 and q995 > 0 else ("High" if flow >= q95 and q95 > 0 else "Moderate")
        alerts.append({"timestamp": r.local_time.strftime("%d %b %Y, %H:%M"), "station_code": int(r.station_code), "flow": flow,
                       "people_in": int(r.people_in), "people_out": int(r.people_out), "severity": severity,
                       "type": "Overcrowding risk" if flow >= q95 and q95 > 0 else "High observed flow",
                       "message": f"Observed passenger flow of {flow:,} at station code {int(r.station_code)}."})
    return alerts


@app.get("/", response_class=HTMLResponse)
def home():
    return (FRONTEND / "index.html").read_text(encoding="utf-8")

@app.get("/api/status")
def status():
    try:
        df = load_data()
        return {"ok": True, "dataset": DATA_FILE.name if DATA_FILE.exists() else CSV_FILE.name, "records": len(df),
                "stations": int(df.station_code.nunique()), "station_limit": SELECTED_STATION_LIMIT,
                "start": df.local_time.min().strftime("%Y-%m-%d %H:%M"),
                "end": df.local_time.max().strftime("%Y-%m-%d %H:%M"), "source_type": "historical", "timezone": "Asia/Seoul",
                "note": f"Dashboard analysis is limited to the first {SELECTED_STATION_LIMIT} station codes in sorted order for performance."}
    except HTTPException as e:
        return {"ok": False, "detail": e.detail}

@app.get("/api/stations")
def stations():
    df = load_data()
    counts = df.groupby("station_code").agg(records=("total_flow", "size"), total_flow=("total_flow", "sum"), avg_flow=("total_flow", "mean")).reset_index()
    return [{"station_code": int(r.station_code), "label": f"Station code {int(r.station_code)}", "records": int(r.records), "total_flow": int(r.total_flow), "avg_flow": round(float(r.avg_flow), 1)} for _, r in counts.sort_values("station_code").iterrows()]

@app.get("/api/overview")
def overview(station_code: int | None = None):
    df = filtered_station(station_code)
    # Summary is calculated over the full loaded period; hourly chart is the most recent 7 days of available data.
    daily = df.groupby("date").agg(people_in=("people_in", "sum"), people_out=("people_out", "sum"), total_flow=("total_flow", "sum")).reset_index()
    recent_dates = sorted(daily.date.unique())[-7:]
    recent = daily[daily.date.isin(recent_dates)]
    return {"total_records": int(len(df)), "station_count": int(df.station_code.nunique()), "total_entries": int(df.people_in.sum()),
            "total_exits": int(df.people_out.sum()), "avg_hourly_flow": round(float(df.total_flow.mean()), 1),
            "peak_hour": int(df.groupby("hour").total_flow.mean().idxmax()), "peak_flow": int(df.total_flow.max()),
            "date_start": df.local_time.min().strftime("%d %b %Y"), "date_end": df.local_time.max().strftime("%d %b %Y"),
            "daily": [{"date": r.date, "entries": int(r.people_in), "exits": int(r.people_out), "flow": int(r.total_flow)} for _, r in recent.iterrows()],
            "alerts": make_alerts(df, 8)}

@app.get("/api/timeseries")
def timeseries(station_code: int | None = None, days: int = Query(7, ge=1, le=365)):
    df = filtered_station(station_code)
    cutoff = df.local_time.max() - pd.Timedelta(days=days)
    part = df[df.local_time >= cutoff]
    hourly = part.groupby(part.local_time.dt.floor("h")).agg(entries=("people_in", "sum"), exits=("people_out", "sum"), flow=("total_flow", "sum")).reset_index()
    # Bound payload size for broad queries.
    if len(hourly) > 1000:
        hourly = hourly.iloc[::math.ceil(len(hourly)/1000)]
    return [{"time": r.local_time.strftime("%Y-%m-%d %H:%M"), "entries": int(r.entries), "exits": int(r.exits), "flow": int(r.flow)} for _, r in hourly.iterrows()]

@app.get("/api/heatmap")
def heatmap():
    df = load_data()
    agg = df.groupby(["station_code", "hour"]).total_flow.mean().reset_index()
    stations_list = sorted(df.station_code.unique().tolist())
    matrix = []
    lookup = {(int(r.station_code), int(r.hour)): round(float(r.total_flow), 1) for _, r in agg.iterrows()}
    for code in stations_list:
        matrix.append({"station_code": int(code), "values": [lookup.get((int(code), h), 0) for h in range(24)]})
    return {"hours": list(range(24)), "stations": matrix, "note": "Mean observed hourly entries + exits, based on historical records."}

@app.get("/api/analytics")
def analytics():
    df = load_data()
    ranking = df.groupby("station_code").agg(total_flow=("total_flow", "sum"), mean_flow=("total_flow", "mean"), records=("total_flow", "size")).reset_index().sort_values("total_flow", ascending=False).head(12)
    hourly = df.groupby("hour").agg(entries=("people_in", "mean"), exits=("people_out", "mean"), flow=("total_flow", "mean")).reset_index()
    return {"top_stations": [{"station_code": int(r.station_code), "total_flow": int(r.total_flow), "avg_flow": round(float(r.mean_flow),1), "records": int(r.records)} for _,r in ranking.iterrows()],
            "hourly": [{"hour": int(r.hour), "entries": round(float(r.entries),1), "exits": round(float(r.exits),1), "flow": round(float(r.flow),1)} for _,r in hourly.iterrows()]}

@app.get("/api/forecast")
def forecast(station_code: int | None = None, horizon: int = Query(12, ge=1, le=48)):
    df = filtered_station(station_code)
    # Transparent baseline: average observed flow for each hour of day.
    hourly = df.groupby("hour").agg(entries=("people_in", "mean"), exits=("people_out", "mean"), flow=("total_flow", "mean"))
    last = df.local_time.max().floor("h")
    result = []
    for i in range(1, horizon+1):
        ts = last + pd.Timedelta(hours=i)
        h = ts.hour
        vals = hourly.loc[h] if h in hourly.index else pd.Series({"entries":0,"exits":0,"flow":0})
        result.append({"time": ts.strftime("%d %b %H:%M"), "hour": h, "entries": round(float(vals.entries),1), "exits": round(float(vals.exits),1), "flow": round(float(vals.flow),1), "method":"historical hourly average"})
    return {"method": "Historical hourly average baseline", "station_code": station_code, "forecast": result,
            "disclaimer": "Indicative baseline, not a validated production forecast."}

@app.get("/api/simulator/next")
def simulator_next(station_code: int | None = None):
    global _sim_index
    df = filtered_station(station_code)
    if df.empty: raise HTTPException(status_code=404, detail="No records available.")
    with _cache_lock:
        row = df.iloc[_sim_index % len(df)]
        _sim_index += 1
        idx = _sim_index
    flow = int(row.total_flow)
    q95 = float(df.total_flow.quantile(.95))
    return {"simulation": True, "index": idx, "timestamp": row.local_time.strftime("%Y-%m-%d %H:%M:%S KST"),
            "station_code": int(row.station_code), "people_in": int(row.people_in), "people_out": int(row.people_out), "flow": flow,
            "risk": "Elevated" if flow >= q95 else "Normal", "source_note": "Replaying an actual historical row; not a live passenger feed."}

@app.get("/api/alerts")
def alerts(limit: int = Query(20, ge=1, le=100)):
    df = load_data()
    items = make_alerts(df, limit)
    critical = sum(x["severity"] == "Critical" for x in items)
    high = sum(x["severity"] == "High" for x in items)
    return {"items": items, "total": len(items), "critical": critical, "high": high, "overcrowding": sum("Overcrowding" in x["type"] for x in items), "note": "Illustrative alerts derived from historical high-flow observations."}

class Announcement(BaseModel):
    station_code: str = Field(min_length=1, max_length=40)
    severity: str = Field(default="Information", max_length=30)
    message: str = Field(min_length=3, max_length=500)

@app.get("/api/announcements")
def list_announcements():
    return {"items": list(reversed(_announcements)), "note": "Stored in server memory for this running session only; not broadcast to passengers."}

@app.post("/api/announcements")
def create_announcement(item: Announcement):
    record = {"station_code": item.station_code.strip(), "severity": item.severity.strip(), "message": item.message.strip(), "created_at": datetime.now(timezone.utc).strftime("%Y-%m-%d %H:%M UTC")}
    _announcements.append(record)
    return {"ok": True, "announcement": record, "note": "Demo-only announcement. It is not sent to Seoul Metro or public displays."}

@app.get("/api/export.csv")
def export_csv(station_code: int | None = None):
    df = filtered_station(station_code)
    out = df[["local_time", "station_code", "people_in", "people_out", "total_flow"]].copy()
    out["timestamp"] = out["local_time"].dt.strftime("%Y-%m-%d %H:%M:%S %Z")
    out = out[["timestamp", "station_code", "people_in", "people_out", "total_flow"]]
    data = out.to_csv(index=False).encode("utf-8")
    return StreamingResponse(iter([data]), media_type="text/csv", headers={"Content-Disposition":"attachment; filename=metroflow_export.csv"})
