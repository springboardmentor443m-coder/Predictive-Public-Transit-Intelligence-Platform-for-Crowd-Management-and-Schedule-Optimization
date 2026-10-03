import os
import sqlite3
import pandas as pd
from typing import Dict, Any

from app.datasets.bmrcl_pipeline import main as run_bmrcl_pipeline

WORKSPACE_ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "..", ".."))
DATA_DIR = os.path.join(WORKSPACE_ROOT, "data")
PROCESSED_DIR = os.path.join(os.path.dirname(__file__), "processed")
DB_PATH = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "..", "metroflow.db"))
PARQUET_PATH = os.path.join(PROCESSED_DIR, "master_bmrcl_ridership.parquet")


class RealWorldDatasetPipeline:
    """
    BMRCL Real-World Transit Dataset Pipeline.
    Manages genuine BMRCL GTFS network topology and August + September 2025 hourly ridership.
    """

    def __init__(self):
        self.data_dir = DATA_DIR
        self.processed_dir = PROCESSED_DIR

    def run_pipeline(self) -> Dict[str, Any]:
        print("[Pipeline] Ingesting genuine BMRCL transit datasets (GTFS & RTI Ridership)...")
        
        # If parquet and database already exist and populated, read stats
        if os.path.exists(PARQUET_PATH):
            df = pd.read_parquet(PARQUET_PATH)
        else:
            run_bmrcl_pipeline()
            df = pd.read_parquet(PARQUET_PATH)

        stats = {
            "total_records": len(df),
            "sources": [
                "BMRCL GTFS (OpenStreetMap & Published Timetable)",
                "BMRCL RTI Ridership (August 2025)",
                "BMRCL RTI Ridership (September 2025)"
            ],
            "date_range": f"{df['timestamp'].min()} to {df['timestamp'].max()}",
            "processed_parquet_path": PARQUET_PATH,
            "unique_stations": int(df["station_code"].nunique()),
            "total_entries": int(df["entries"].sum()),
            "total_exits": int(df["exits"].sum()),
        }
        print(f"[Pipeline Complete] Genuine BMRCL dataset ready ({len(df):,} records)")
        return stats


pipeline_engine = RealWorldDatasetPipeline()

if __name__ == "__main__":
    pipeline_engine.run_pipeline()
