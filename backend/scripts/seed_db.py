import argparse
import os
import sys
from datetime import datetime, timedelta

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

import pandas as pd  # noqa: E402

from app.core.database import Base, SessionLocal, engine  # noqa: E402
from app.core.security import hash_password  # noqa: E402
from app.core.time import utcnow  # noqa: E402
from app.ml import features as feat  # noqa: E402
from app.models import alert, ridership, schedule, station, train, user  # noqa: E402,F401
from app.services import simulation as sim  # noqa: E402

DATA_DIR = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "data")

USERS = [
    ("admin@metroflow.io", "Admin@123", "Alex Morgan", "admin"),
    ("operator@metroflow.io", "Operator@123", "Priya Sharma", "operator"),
    ("viewer@metroflow.io", "Viewer@123", "Jordan Lee", "viewer"),
]


HISTORY_DAYS = sim.HISTORY_DAYS


def _congestion_level(occ_pct: float) -> str:
    return sim.congestion_level(occ_pct)


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
    hourly records from the baseline occupancy curve.

    Days are anchored to *midnight* and the current partial day is appended, so
    every record sits on the hour it actually describes and the newest sample is
    the current hour. Anchoring the day to `now` instead shifted the entire
    series forward by the current hour-of-day, which transposed the morning peak
    onto whatever wall-clock time the seed happened to run.

    Generation is delegated to the simulation clock's per-hour builder so these
    rows are byte-identical to the ones it would produce at runtime.
    """
    now = sim.hour_floor()
    midnight = now.replace(hour=0)
    stations = [(str(r["code"]), int(r["capacity_per_hour"]))
                for _, r in stations_df.iterrows()]

    # The plan buckets on **UTC** hours deliberately. A local day is 23 or 25 hours
    # long across a DST change, so `range(24)` over a local day would either skip or
    # duplicate an hour. Walking UTC hours and letting `ridership_rows_for_hour`
    # localise each one gives gap-free, overlap-free coverage on both transition
    # days, and the local hour is still what labels the occupancy curve.
    day_plan: list[tuple[datetime, range]] = [
        (midnight - timedelta(days=d), range(24)) for d in range(HISTORY_DAYS, 0, -1)
    ]
    day_plan.append((midnight, range(now.hour + 1)))

    rows = []
    for day_start, hours in day_plan:
        for hour in hours:
            rows.extend(sim.ridership_rows_for_hour(stations, day_start + timedelta(hours=hour)))
    print(f"  ridership_hourly.csv missing/empty; synthesized {HISTORY_DAYS}d + today "
          f"of baseline history (now-anchored, hour-aligned)")
    return rows


def _build_ridership_rows(stations_df: pd.DataFrame) -> list:
    now = utcnow()
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


def _seeded_deletions(db) -> list:
    """Row sets owned by the seed pipeline.

    Identified by id prefix so `--refresh` can roll the demo window forward
    without touching anything created by users: ingests use `RR-ING-*` and
    operator-created schedules keep their own ids.
    """
    return [
        db.query(schedule.TrainSchedule).filter(schedule.TrainSchedule.id.like("SCH-%")),
        db.query(ridership.RidershipRecord).filter(
            ridership.RidershipRecord.id.like("RR-%"),
            ridership.RidershipRecord.id.notlike("RR-ING-%"),
        ),
        db.query(alert.Alert).filter(alert.Alert.id.like("AL-SEED-%")),
    ]


def _clear_seeded_db(db) -> int:
    removed = 0
    for query in _seeded_deletions(db):
        targets = query.all()
        removed += len(targets)
        for row in targets:
            db.delete(row)
    db.commit()
    return removed


def _fleet_for_lines(lines: list[str]) -> list[dict]:
    """One fleet per trunk route, from real MTA rolling-stock classes."""
    fleet = []
    for line in lines:
        for n in range(1, feat.FLEET_PER_LINE + 1):
            model, capacity = feat.ROLLING_STOCK[(n - 1) % len(feat.ROLLING_STOCK)]
            fleet.append({
                "id": feat.train_code(line, n),
                "model": model,
                "capacity": capacity,
                # One unit per route is held in the depot so the fleet monitor
                # always shows an out-of-service state to dispatch against.
                "status": "active" if n < feat.FLEET_PER_LINE else "maintenance",
            })
    return fleet


def _station_row(index: int, row: pd.Series) -> station.Station:
    return station.Station(
        id=str(row["code"]),
        code=str(row["code"]),
        name=str(row["name"]),
        line=str(row["line"]),
        # The subway has no fare zones, so zone is a synthetic grouping derived
        # from the station's position in the network ordering. Real geography
        # (lat/lng) comes straight from the GTFS feed.
        zone="Zone-" + str(1 + index % 3),
        lat=float(row["lat"]),
        lng=float(row["lng"]),
        capacity_per_hour=int(row["capacity_per_hour"]),
    )


def _network_drift(db, stations_df: pd.DataFrame, fleet: list[dict]) -> dict:
    """Compare data/stations.csv against the database.

    Re-seeding a database whose stations predate the current CSV would leave
    orphaned ridership/schedules pointing at removed stations, so the seed
    detects drift and rebuilds the derived rows.
    """
    wanted_codes = [str(c) for c in stations_df["code"]]
    db_stations = {s.id: s for s in db.query(station.Station).all()}
    db_trains = {t.id for t in db.query(train.Train).all()}

    stale_stations = sorted(set(db_stations) - set(wanted_codes))
    missing_stations = sorted(set(wanted_codes) - set(db_stations))
    changed = []
    for code in wanted_codes:
        if code not in db_stations:
            continue
        row = stations_df[stations_df["code"].astype(str) == code].iloc[0]
        current = db_stations[code]
        if (current.name != str(row["name"]) or current.line != str(row["line"])
                or current.capacity_per_hour != int(row["capacity_per_hour"])):
            changed.append(code)

    return {
        "stale_stations": stale_stations,
        "missing_stations": missing_stations,
        "changed_stations": changed,
        "stale_trains": sorted(db_trains - {t["id"] for t in fleet}),
        "missing_trains": sorted({t["id"] for t in fleet} - db_trains),
    }


def _sync_network(db, stations_df: pd.DataFrame, fleet: list[dict]) -> None:
    """Make the stations/trains tables match data/stations.csv.

    Existing rows are updated in place so their ridership and schedule history
    survives; rows whose code is gone from the CSV are removed together with
    everything that referenced them.
    """
    wanted_codes = [str(c) for c in stations_df["code"]]
    db_stations = {s.id: s for s in db.query(station.Station).all()}

    stale = set(db_stations) - set(wanted_codes)
    if stale:
        print(f"  Removing {len(stale)} station(s) no longer in stations.csv ...")
        for model, column in (
            (ridership.RidershipRecord, ridership.RidershipRecord.station_id),
            (schedule.TrainSchedule, schedule.TrainSchedule.station_id),
            (alert.Alert, alert.Alert.station_id),
        ):
            for row in db.query(model).filter(column.in_(sorted(stale))).all():
                db.delete(row)
        for code in sorted(stale):
            db.delete(db_stations[code])

    added = 0
    for i, (_, row) in enumerate(stations_df.iterrows()):
        code = str(row["code"])
        if code in db_stations:
            continue
        db.add(_station_row(i, row))
        added += 1
    if added:
        print(f"  Added {added} station(s) from stations.csv")

    for spec in fleet:
        existing = db.query(train.Train).filter(train.Train.id == spec["id"]).first()
        if existing:
            existing.model = spec["model"]
            existing.capacity = spec["capacity"]
            existing.status = spec["status"]
        else:
            db.add(train.Train(
                id=spec["id"],
                code=spec["id"],
                model=spec["model"],
                capacity=spec["capacity"],
                status=spec["status"],
            ))

    db_trains = {t.id for t in db.query(train.Train).all()}
    orphan_trains = db_trains - {spec["id"] for spec in fleet}
    if orphan_trains:
        print(f"  Removing {len(orphan_trains)} train(s) outside the current fleet ...")
        for row in db.query(schedule.TrainSchedule).filter(
            schedule.TrainSchedule.train_id.in_(sorted(orphan_trains))
        ).all():
            db.delete(row)
        for row in db.query(alert.Alert).filter(alert.Alert.train_id.in_(sorted(orphan_trains))).all():
            db.delete(row)
        for code in sorted(orphan_trains):
            db.delete(db.query(train.Train).filter(train.Train.id == code).first())
    db.commit()


def seed(refresh: bool = False) -> None:
    print("Creating tables ...")
    Base.metadata.create_all(bind=engine)
    db = SessionLocal()

    stations_df = pd.read_csv(os.path.join(DATA_DIR, "stations.csv"), dtype={"code": str})
    lines = sorted(stations_df["line"].unique())
    fleet = _fleet_for_lines(lines)

    users_exist = db.query(user.User).count() > 0
    drift = _network_drift(db, stations_df, fleet)
    has_drift = any(drift[k] for k in (
        "stale_stations", "missing_stations", "changed_stations",
        "stale_trains", "missing_trains",
    ))

    if users_exist and not refresh and not has_drift:
        print("Database already seeded and up to date; skipping. "
              "Use `--refresh` to roll the demo window forward.")
        db.close()
        return

    if refresh:
        removed = _clear_seeded_db(db)
        print(f"Refresh mode: cleared {removed} seeded rows (schedules/history/alerts).")
    elif has_drift:
        # Station or fleet identity changed underneath us, so every derived row
        # is rebuilt: schedules/history/alerts reference station and train ids.
        removed = _clear_seeded_db(db)
        print(f"stations.csv differs from the database; rebuilt {removed} dependent rows.")

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

    print(f"Syncing {len(stations_df)} stations and {len(fleet)} trains from stations.csv ...")
    _sync_network(db, stations_df, fleet)

    print("Seeding schedules (7-day history + next 24h rolling window) ...")
    now = sim.hour_floor()
    _train_map = [t.code for t in db.query(train.Train).all() if t.code]
    gen_start = now - timedelta(days=HISTORY_DAYS)
    gen_hours = HISTORY_DAYS * 24 + 24
    sched_count = 0
    for line in lines:
        line_stations = [c for c, r in zip(stations_df["code"], stations_df["line"]) if r == line]
        # Same headway/disruption model the runtime simulation clock uses, so a
        # seeded hour and a clock-generated hour are identical.
        line_trains = sim._fleet_for_line(_train_map, line, line_stations)
        for t_idx, tcode in enumerate(line_trains):
            for i in range(gen_hours):
                for row in sim.schedule_rows_for_hour(
                    line_stations, tcode, t_idx, gen_start + timedelta(hours=i)
                ):
                    db.add(row)
                    sched_count += 1
    db.commit()
    print(f"  {sched_count} schedules created")

    print("Seeding ridership history (last 7 days, now-anchored) ...")
    rows = _build_ridership_rows(stations_df)
    db.bulk_save_objects(rows)
    db.commit()
    print(f"  {len(rows)} ridership records inserted")

    print("Seeding sample alerts ...")
    # Anchor the samples on the busiest real stations so the alert feed reads
    # like something an operator would actually see on this network.
    busiest = stations_df.sort_values("capacity_per_hour", ascending=False)
    hub = str(busiest.iloc[0]["code"])
    hub_name = str(busiest.iloc[0]["name"])
    second = str(busiest.iloc[1]["code"])
    second_name = str(busiest.iloc[1]["name"])
    db.add(alert.Alert(
        id="AL-SEED-001", type="overcrowding", severity="high", station_id=hub,
        title=f"High congestion at {hub_name}",
        message="Platform occupancy exceeded 90% during morning peak. Consider additional services.",
    ))
    db.add(alert.Alert(
        id="AL-SEED-002", type="delay", severity="medium", station_id=second,
        title=f"Signalling delay approaching {second_name}",
        message="A train is running several minutes late approaching the stop; passengers are advised to allow extra time.",
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
