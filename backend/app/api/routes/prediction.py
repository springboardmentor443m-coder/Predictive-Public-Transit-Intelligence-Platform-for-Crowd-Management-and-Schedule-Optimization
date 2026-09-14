import pandas as pd
from fastapi import APIRouter, Depends, Query
from sqlalchemy.orm import Session
from app.db.database import get_db
from app.models.transit import Ridership, Station
from app.ml.data_loader import load_ridership_df
from app.ml.predictor import load_bundle, forecast
from app.core.config import settings
from app.services.crowd import congestion_level, recommend_frequency
from app.core.deps import get_current_user

router = APIRouter(prefix="/api/predictions", tags=["prediction"], dependencies=[Depends(get_current_user)])

MODEL_PATH = Path = None
from pathlib import Path as _P
MODEL_FILE = _P(__file__).resolve().parents[3] / "model.pkl"
ALT_MODEL = _P(__file__).resolve().parent.parent / "ml" / "model.pkl"


def _bundle():
    for p in (MODEL_FILE, ALT_MODEL, _P(settings.model_path)):
        b = load_bundle(str(p))
        if b is not None:
            return b
    return None


def _station_df(db: Session, code: str) -> pd.DataFrame:
    rows = (db.query(Ridership).filter(Ridership.station_code == code)
            .order_by(Ridership.timestamp).all())
    if rows:
        return pd.DataFrame([{"station_code": r.station_code, "timestamp": r.timestamp,
                              "entries": r.entries, "exits": r.exits} for r in rows])
    df = load_ridership_df(settings.data_path)
    return df[df["station_code"] == code].copy()


@router.get("/crowd")
def predict_crowd(station_code: str, hours: int = Query(24, le=72), db: Session = Depends(get_db)):
    bundle = _bundle()
    sdf = _station_df(db, station_code)
    if sdf.empty:
        return {"station_code": station_code, "forecast": []}
    if bundle is None:
        # Fallback: naive weekly-seasonal baseline (no model file yet)
        hist = sdf.sort_values("timestamp").tail(24 * 7)
        last = sdf["timestamp"].max()
        base = hist.groupby(hist["timestamp"].dt.hour)["entries"].mean()
        out = []
        for h in range(1, hours + 1):
            ts = last + pd.Timedelta(hours=h)
            e = float(base.get(ts.hour, sdf["entries"].mean()))
            t = e * 1.92
            out.append({"timestamp": ts, "predicted_entries": round(e, 1),
                        "predicted_exits": round(e * 0.92, 1),
                        "predicted_total": round(t, 1), "congestion": congestion_level(t)})
        return {"station_code": station_code, "model": "baseline-seasonal", "forecast": out}
    fc = forecast(sdf, bundle, hours)
    fc["congestion"] = fc["predicted_total"].apply(congestion_level)
    return {"station_code": station_code, "model": "random-forest",
            "forecast": fc.to_dict(orient="records")}


@router.get("/demand")
def demand(station_code: str, hours: int = Query(24, le=72), db: Session = Depends(get_db)):
    res = predict_crowd(station_code, hours, db)
    fc = res["forecast"]
    total = sum(f["predicted_total"] for f in fc)
    peak = max(fc, key=lambda f: f["predicted_total"]) if fc else None
    return {"station_code": station_code, "window_hours": hours,
            "total_predicted_pax": round(total, 1),
            "avg_per_hour": round(total / max(1, hours), 1), "peak_hour": peak}


@router.get("/peak-hours")
def peak_hours(station_code: str, db: Session = Depends(get_db)):
    df = load_ridership_df(settings.data_path)
    g = df[df["station_code"] == station_code].copy()
    if g.empty:
        return {"station_code": station_code, "peak_hours": []}
    g["hour"] = g["timestamp"].dt.hour
    agg = g.groupby("hour")[["entries", "exits"]].mean()
    agg["total"] = agg["entries"] + agg["exits"]
    top = agg.sort_values("total", ascending=False).head(4)
    return {"station_code": station_code,
            "peak_hours": [{"hour": int(h), "avg_total": round(float(r['total']), 1),
                            "congestion": congestion_level(float(r["total"]))}
                           for h, r in top.iterrows()]}


@router.get("/recommendations")
def recommendations(station_code: str, hours: int = Query(6, le=24), db: Session = Depends(get_db)):
    res = predict_crowd(station_code, hours, db)
    st = db.query(Station).filter(Station.code == station_code).first()
    cap = st.capacity_per_hour if st else 5000
    out = []
    for f in res["forecast"][:hours]:
        rec = recommend_frequency(f["predicted_total"], cap)
        out.append({"timestamp": f["timestamp"], "predicted_total": f["predicted_total"],
                    "congestion": f["congestion"], **rec})
    worst = max(out, key=lambda x: x["load_factor"]) if out else None
    return {"station_code": station_code, "capacity_per_hour": cap,
            "recommendations": out,
            "summary": f"Peak load {worst['load_factor']*100:.0f}% at {worst['timestamp']} -> run every {worst['frequency_min']} min ({worst['action']})." if worst else "No data."}
