"""Seed DB from ridership CSV + synthetic stations/schedules."""
import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parents[2]))

import pandas as pd
from app.db.database import Base, engine, SessionLocal
from app.models.user import User  # noqa
from app.models.transit import Station, Ridership, Schedule  # noqa
from app.ml.data_loader import load_ridership_df
from app.core.config import settings
from app.core.security import get_password_hash

LINES = ["1", "2", "3", "A", "C"]
# Approx NYC coords jitter around Manhattan
BASE_LAT, BASE_LON = 40.7580, -73.9855


def main(limit_stations: int = 12, max_rows: int = 20000):
    Base.metadata.create_all(bind=engine)
    df = load_ridership_df(settings.data_path)
    codes = sorted(df["station_code"].unique().tolist())[:limit_stations]
    df = df[df["station_code"].isin(codes)].sort_values(["station_code", "timestamp"]).tail(max_rows)
    print(f"Seeding {len(codes)} stations, {len(df)} ridership rows")

    db = SessionLocal()
    try:
        # users
        for uname, pwd, role, name in [("admin", "admin123", "admin", "Metro Admin"),
                                       ("operator", "operator123", "operator", "Station Operator")]:
            if not db.query(User).filter(User.username == uname).first():
                db.add(User(username=uname, full_name=name,
                            hashed_password=get_password_hash(pwd), role=role))
        # stations
        for i, code in enumerate(codes):
            if not db.query(Station).filter(Station.code == code).first():
                db.add(Station(code=code, name=str(code).replace("_", " ").title(),
                               line=LINES[i % len(LINES)],
                               latitude=BASE_LAT + (i * 0.008) % 0.12 - 0.06,
                               longitude=BASE_LON + (i * 0.011) % 0.14 - 0.07,
                               capacity_per_hour=5000))
        db.commit()
        # ridership (replace for these stations)
        db.query(Ridership).filter(Ridership.station_code.in_(codes)).delete()
        db.commit()
        recs = [Ridership(station_code=r.station_code, timestamp=r.timestamp,
                          entries=int(r.entries), exits=int(r.exits))
                for r in df.itertuples()]
        for i in range(0, len(recs), 1000):
            db.bulk_save_objects(recs[i:i + 1000])
            db.commit()
        # schedules: 4 departures per station
        db.query(Schedule).delete()
        db.commit()
        scheds = []
        for code in codes:
            st = db.query(Station).filter(Station.code == code).first()
            for dep in ("08:00", "09:00", "17:30", "18:30"):
                scheds.append(Schedule(line=st.line, station_code=code, direction="Northbound",
                                       departure=dep, frequency_min=6, status="ontime", delay_min=0))
        db.bulk_save_objects(scheds)
        db.commit()
        print("Seed complete.")
    finally:
        db.close()


if __name__ == "__main__":
    main()
