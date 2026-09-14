import pandas as pd
from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session
from app.db.database import get_db
from app.models.transit import Ridership, Station, Schedule, Alert
from app.services.crowd import congestion_level
from app.core.deps import get_current_user

router = APIRouter(prefix="/api/analytics", tags=["analytics"], dependencies=[Depends(get_current_user)])


@router.get("/traffic")
def traffic(db: Session = Depends(get_db)):
    rows = db.query(Ridership).order_by(Ridership.timestamp.desc()).limit(5000).all()
    if not rows:
        return {"hourly": []}
    df = pd.DataFrame([{"timestamp": r.timestamp, "total": (r.entries or 0) + (r.exits or 0)} for r in rows])
    df["timestamp"] = pd.to_datetime(df["timestamp"]).dt.floor("h")
    agg = df.groupby("timestamp")["total"].sum().reset_index().sort_values("timestamp")
    return {"hourly": [{"timestamp": t, "total": int(v)} for t, v in zip(agg["timestamp"].astype(str), agg["total"]) ]}


@router.get("/station-performance")
def station_perf(db: Session = Depends(get_db)):
    rows = db.query(Ridership).order_by(Ridership.timestamp.desc()).limit(8000).all()
    agg: dict = {}
    for r in rows:
        d = agg.setdefault(r.station_code, {"entries": 0, "exits": 0, "n": 0})
        d["entries"] += r.entries or 0
        d["exits"] += r.exits or 0
        d["n"] += 1
    names = {s.code: s.name for s in db.query(Station).all()}
    out = []
    for code, d in agg.items():
        total = d["entries"] + d["exits"]
        avg = total / max(1, d["n"])
        out.append({"station_code": code, "station_name": names.get(code, code),
                    "total_pax": total, "avg_per_hour": round(avg, 1),
                    "congestion": congestion_level(avg)})
    return sorted(out, key=lambda x: x["total_pax"], reverse=True)


@router.get("/operational")
def operational(db: Session = Depends(get_db)):
    total_s = db.query(Schedule).count()
    delayed = db.query(Schedule).filter(Schedule.status == "delayed").count()
    alerts = db.query(Alert).count()
    crit = db.query(Alert).filter(Alert.severity.in_(["high", "critical"])).count()
    delay_rate = round(100 * delayed / max(1, total_s), 2)
    return {"scheduled_trips": total_s, "delayed_trips": delayed,
            "delay_rate_pct": delay_rate, "total_alerts": alerts,
            "critical_alerts": crit,
            "on_time_pct": round(100 - delay_rate, 2)}


@router.get("/kpis")
def kpis(db: Session = Depends(get_db)):
    op = operational(db)
    perf = station_perf(db)
    avg_cong = {}
    for p in perf:
        avg_cong[p["congestion"]] = avg_cong.get(p["congestion"], 0) + 1
    return {**op, "stations_by_congestion": avg_cong, "top_station": perf[0] if perf else None}
