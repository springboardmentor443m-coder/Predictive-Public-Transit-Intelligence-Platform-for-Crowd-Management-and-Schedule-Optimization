import os
import sqlite3
import pandas as pd
from typing import List, Dict, Any

DB_PATH = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "..", "metroflow.db"))
PARQUET_PATH = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "datasets", "processed", "master_bmrcl_ridership.parquet"))


def load_bmrcl_stations() -> List[Dict[str, Any]]:
    """Loads the genuine 83 BMRCL stations from the relational database."""
    if not os.path.exists(DB_PATH):
        # Fallback to direct GTFS read if DB not initialized yet
        from app.datasets.bmrcl_pipeline import run_gtfs_ingestion
        stations, _ = run_gtfs_ingestion()
        return stations

    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    cursor.execute("""
        SELECT id, station_code, name, line_name, platform_capacity, latitude, longitude, sequence_order, is_interchange
        FROM stations
        ORDER BY id
    """)
    rows = cursor.fetchall()
    conn.close()

    stations = []
    for r in rows:
        stations.append({
            "id": r[0],
            "code": r[1],
            "station_code": r[1],
            "name": r[2],
            "line": r[3],
            "line_name": r[3],
            "capacity": r[4],
            "platform_capacity": r[4],
            "lat": r[5],
            "latitude": r[5],
            "lng": r[6],
            "longitude": r[6],
            "seq": r[7],
            "sequence_order": r[7],
            "interchange": bool(r[8]),
            "is_interchange": bool(r[8]),
        })
    return stations


# Canonical Station Metadata for BMRCL Network
STATION_METADATA = load_bmrcl_stations()


def get_real_bmrcl_transit_dataset() -> pd.DataFrame:
    """Loads the genuine 92,280 BMRCL passenger records without any synthetic modification."""
    if os.path.exists(PARQUET_PATH):
        return pd.read_parquet(PARQUET_PATH)
    
    conn = sqlite3.connect(DB_PATH)
    df = pd.read_sql_query("SELECT * FROM passenger_counts ORDER BY timestamp", conn)
    conn.close()
    return df
