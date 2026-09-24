import argparse
import os
import sys
from datetime import datetime, timedelta, timezone

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

import pandas as pd  # noqa: E402

from app.core.database import Base, SessionLocal, engine  # noqa: E402
from app.core.security import hash_password  # noqa: E402
from app.ml import features as feat  # noqa: E402
from app.models import alert, ridership, schedule, station, train, user  # noqa: E402,F401

DATA_DIR = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "data")

STATION_CODES = ["ST01", "ST02", "ST03", "ST04", "ST05", "ST06", "ST07", "ST08", "ST09", "ST10"]

USERS = [
    ("admin@metroflow.io", "Admin@123", "Alex Morgan", "admin"),
    ("operator@metroflow.io", "Operator@123", "Priya Sharma", "operator"),
    ("viewer@metroflow.io", "Viewer@123", "Jordan Lee", "viewer"),
]


HISTORY_DAYS = 7


def _congestion_level(occ_pct: float) -> str:
    if occ_pct >= 0.90:
        return "critical"
    if occ_pct >= 0.75:
        return "high"
    if occ_pct >= 0.55:
        return "medium"
    return "low"


def _rows_from_dataframe(hist: pd.DataFrame) -> list:
    """Take the newest HISTORY_DAYS available in the dataset — not relative to
    wall clock — so stale CSVs still seed a usable history window."""
    newest = hist["timestamp"].max()
    cutoff = newest.normalize() - pd.Timedelta(days=HISTORY_DAYS)
    recent = hist[hist["timestamp"] >= cutoff]
    rows = []
    for _, r in recent.iterrows():
        code = r["station_code"]
        ts = r["timestamp"].to_pydatetime()
        rows.append(ridership.RidershipRecord(
            id=f"RR-{code}-{int(r['timestamp'].timestamp())}",
            station_id=code,
            timestamp=ts,
            entries=int(r["entries"]),
            exits=int(r["exits"]),
            occupancy=int(r["occupancy"]),
            congestion_level=r["congestion_level"],
        ))
    print(f"  dataset window: {newest} (using {len(rows)} rows)")
    return rows


def _synthetic_rows(stations_df: pd.DataFrame) -> list:
    """Fallback when the CSV is missing/empty: synthesize HISTORY_DAYS of
    hourly records from the baseline occupancy curve."""
    now = datetime.now(timezone.utc).replace(tzinfo=None, minute=0, second=0, microsecond=0)
    rows = []
    for i, row in stations_df.iterrows():
        cap = int(row["capacity_per_hour"])
        factor = 0.85 + 0.05 * ((i * 37) % 7)
        for d in range(HISTORY_DAYS, 0, -1):
            day = now - timedelta(days=d)
            weekend = day.weekday() >= 5
            for hour in range(24):
                ts = day + timedelta(hours=hour)
                pct = feat.station_baseline_occupancy_pct(hour)
                if weekend:
                    pct *= feat.WEEKEND_FACTOR
                pct = min(1.15, max(0.02, pct * factor))
                rows.append(ridership.RidershipRecord(
                    id=f"RR-{row['code']}-{int(ts.timestamp())}",
                    station_id=row["code"],
                    timestamp=ts,
                    entries=int(cap * pct / 4),
                    exits=int(cap * pct / 4 * 0.9),
                    occupancy=int(cap * pct / 4),
                    congestion_level=_congestion_level(pct),
                ))
    print("  ridership_hourly.csv missing or empty; synthesized baseline history")
    return rows


def _build_ridership_rows(stations_df: pd.DataFrame) -> list:
    now = datetime.now(timezone.utc).replace(tzinfo=None)
    ridership_path = os.path.join(DATA_DIR, "ridership_hourly.csv")
    hist = None
    if os.path.exists(ridership_path):
        try:
            hist = pd.read_csv(ridership_path, parse_dates=["timestamp"])
        except Exception as e:
            print(f"  Could not parse {ridership_path} ({e}); falling back.")
    if hist is None or hist.empty or "timestamp" not in hist.columns:
        return _synthetic_rows(stations_df)
    # Prefer the CSV only when it is reasonably fresh (<= 3 days old); otherwise
    # synthesize a rolling window ending *now* so the "last 24h" dashboards and
    # freshness of the demo data are always up to date.
    if hist["timestamp"].max() < now - timedelta(days=3):
        print("  ridership_hourly.csv is stale; synthesizing a now-anchored window instead.")
        return _synthetic_rows(stations_df)
    rows = _rows_from_dataframe(hist)
    return rows if rows else _synthetic_rows(stations_df)


def _clear_seeded_db(db) -> int:
    """Remove only prefix-identifiable seeded rows so `--refresh` can roll the
    demo window forward without touching anything created by users (ingests
    use RR-ING-*, operator-created schedules keep their own ids)."""
    removed = 0
    for model, prefix in (
        (schedule.TrainSchedule, "SCH-"),
        (ridership.RidershipRecord, "RR-ST"),
        (alert.Alert, "AL-SEED-"),
    ):
        targets = db.query(model).filter(model.id.like(f"{prefix}%")).all()
        removed += len(targets)
        for row in targets:
            db.delete(row)
    db.commit()
    return removed


def seed(refresh: bool = False) -> None:
    print("Creating tables ...")
    Base.metadata.create_all(bind=engine)
    db = SessionLocal()

    users_exist = db.query(user.User).count() > 0
    stations_exist = db.query(station.Station).count() > 0

    if users_exist and not refresh:
        print("Database already seeded; skipping. Use `--refresh` to roll the demo window forward.")
        db.close()
        return

    if refresh:
        removed = _clear_seeded_db(db)
        print(f"Refresh mode: cleared {removed} seeded rows (schedules/history/alerts).")

    if not users_exist:
        print("Seeding users ...")
        for email, pwd, name, role in USERS:
            db.add(user.User(
                id=f"usr_{role}",
                email=email,
                full_name=name,
                hashed_password=hash_password(pwd),
                role=role,
                is_active=True,
            ))

    if not stations_exist:
        print("Seeding stations ...")
        stations_path = os.path.join(DATA_DIR, "stations.csv")
        stations_df = pd.read_csv(stations_path)
        station_map = {}
        for i, row in stations_df.iterrows():
            sid = row["code"]
            station_map[row["code"]] = sid
            db.add(station.Station(
                id=sid,
                code=row["code"],
                name=row["name"],
                line=row["line"],
                zone="Zone-" + str(1 + i % 3),
                lat=12.90 + i * 0.021,
                lng=77.50 + (i % 5) * 0.031,
                capacity_per_hour=int(row["capacity_per_hour"]),
            ))

    stations_df = pd.read_csv(os.path.join(DATA_DIR, "stations.csv"))
    if not stations_exist:
        print("Seeding trains ...")
        train_map = {}
        lines = sorted(stations_df["line"].unique())
        tid = 1
        for line in lines:
            for n in range(4):
                code = f"TR-{line[0]}{tid:02d}"
                train_map[code] = code
                db.add(train.Train(
                    id=code,
                    code=code,
                    model="MetroCoach-M8" if n % 2 == 0 else "MetroCoach-M6",
                    capacity=1200 if n % 2 == 0 else 900,
                    status="active" if n < 3 else "maintenance",
                ))
                tid += 1
        db.commit()
    else:
        lines = sorted(stations_df["line"].unique())

    print("Seeding schedules (7-day history + next 24h rolling window) ...")
    now = datetime.utcnow().replace(minute=0, second=0, microsecond=0)
    peak_hours = {7, 8, 9, 16, 17, 18}
    _train_map = {t.code: t.id for t in db.query(train.Train).all()}
    gen_start = now - timedelta(days=HISTORY_DAYS)
    gen_hours = HISTORY_DAYS * 24 + 24
    sched_count = 0
    for line in lines:
        line_stations = [c for c, r in zip(stations_df["code"], stations_df["line"]) if r == line]
        line_trains = [t for t in _train_map if t.startswith(f"TR-{line[0]}")][:3]
        for t_idx, tcode in enumerate(line_trains):
            offset = t_idx * 53
            for i in range(gen_hours):
                ts = gen_start + timedelta(hours=i, minutes=offset % 60)
                hour = ts.hour
                headway = 4 if hour in peak_hours else 8
                st_code = line_stations[(hour + t_idx) % len(line_stations)]
                if hour in peak_hours:
                    disrupted = line_stations[ts.day % len(line_stations)]
                    if st_code == disrupted:
                        delay = 5 + ((ts.hour + t_idx) % 3)
                    else:
                        delay = int((sched_count * 7) % 4)
                else:
                    delay = 0
                status = "on_time" if delay <= 2 else "delayed"
                db.add(schedule.TrainSchedule(
                    id=f"SCH-{tcode}-{ts.strftime('%m%d%H%M')}-{st_code}",
                    train_id=tcode,
                    station_id=st_code,
                    direction=("northbound" if (hour + t_idx) % 2 == 0 else "southbound"),
                    arrival=ts,
                    departure=ts + timedelta(seconds=30),
                    headway_min=headway,
                    status=status,
                    delay_min=delay,
                    is_peak="yes" if hour in peak_hours else "no",
                ))
                sched_count += 1
    db.commit()
    print(f"  {sched_count} schedules created")

    print("Seeding ridership history (last 7 days, now-anchored) ...")
    rows = _build_ridership_rows(stations_df)
    db.bulk_save_objects(rows)
    db.commit()
    print(f"  {len(rows)} ridership records inserted")

    print("Seeding sample alerts ...")
    db.add(alert.Alert(
        id="AL-SEED-001", type="overcrowding", severity="high", station_id="ST01",
        title="High congestion at Central Junction",
        message="Platform occupancy exceeded 90% during morning peak. Consider additional services.",
    ))
    db.add(alert.Alert(
        id="AL-SEED-002", type="delay", severity="medium", station_id="ST05",
        title="Train TR-B07 running 6 min late",
        message="Signal regeneration at Stadium Plaza caused a minor delay on the Blue Line.",
    ))
    db.commit()

    seed_mongo_events()

    print("Seed complete.")
    db.close()


def seed_mongo_events() -> None:
    """Best-effort: load sample ticketing/sensor events into MongoDB."""
    try:
        from app.core.mongo import get_sensor_events_collection

        coll = get_sensor_events_collection()
        if coll is None:
            print("MongoDB unavailable - skipping sensor event seeding.")
            return
        if coll.estimated_document_count() > 0:
            print(f"MongoDB already has {coll.estimated_document_count()} events - skipping.")
            return

        path = os.path.join(DATA_DIR, "ticketing_events.csv")
        if not os.path.exists(path):
            print("ticketing_events.csv missing - skipping Mongo seeding.")
            return

        events = pd.read_csv(path, parse_dates=["timestamp"]).head(5000)
        docs = []
        for _, r in events.iterrows():
            docs.append({
                "event_type": "ticketing_swipe",
                "event_id": r["event_id"],
                "station_code": r["station_code"],
                "timestamp": r["timestamp"].to_pydatetime(),
                "card_type": r["card_type"],
                "direction": r["direction"],
                "gate_id": r["gate_id"],
                "fare_amount": float(r["fare_amount"]),
                "source": "seed_dataset",
            })
        coll.insert_many(docs)
        print(f"  {len(docs)} ticketing events inserted into MongoDB")
    except Exception as e:
        print(f"MongoDB seeding skipped ({e}).")


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Seed (or refresh) MetroFlow demo data.")
    parser.add_argument(
        "--refresh",
        action="store_true",
        help="Roll the demo window forward: replace seeded schedules/history/alerts "
        "with now-anchored data (keeps users, stations, trains and user-created rows).",
    )
    args = parser.parse_args()
    seed(refresh=args.refresh)
