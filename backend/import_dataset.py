import argparse
import csv
import os
from pathlib import Path
from typing import Any

from pymongo import MongoClient

from main import load_turnstile_csv


PROJECT_ROOT = Path(__file__).resolve().parent.parent
DEFAULT_SOURCE_PATH = PROJECT_ROOT / "data" / "metroflow_processed_network.csv"


def load_processed_csv(path: Path) -> tuple[list[dict[str, Any]], list[dict[str, Any]]]:
    with path.open("r", encoding="utf-8-sig", newline="") as file:
        rows = list(csv.DictReader(file))

    required_columns = {
        "station_code",
        "station_name",
        "timestamp",
        "entries",
        "exits",
        "passenger_count",
        "capacity",
    }
    if not rows or not required_columns.issubset(rows[0]):
        return [], []

    stations_by_id: dict[str, dict[str, Any]] = {}
    records: list[dict[str, Any]] = []
    for row in rows:
        station_id = f"SEOUL-{row['station_code']}"
        stations_by_id.setdefault(
            station_id,
            {
                "station_id": station_id,
                "name": row["station_name"],
                "capacity": int(float(row["capacity"])),
                "latitude": float(row["latitude"]) if row.get("latitude") else None,
                "longitude": float(row["longitude"]) if row.get("longitude") else None,
            },
        )
        records.append(
            {
                "station_id": station_id,
                "station_name": row["station_name"],
                "timestamp": row["timestamp"],
                "entries": int(float(row["entries"])),
                "exits": int(float(row["exits"])),
                "passenger_count": int(float(row["passenger_count"])),
                "occupancy_rate": float(row["occupancy_rate"]),
                "crowd_level": row["crowd_level"],
                "is_peak_hour": int(row["is_peak_hour"]),
            }
        )

    return list(stations_by_id.values()), records


def load_source_dataset(path: Path) -> tuple[list[dict[str, Any]], list[dict[str, Any]]]:
    with path.open("r", encoding="utf-8-sig", newline="") as file:
        columns = set(csv.DictReader(file).fieldnames or [])

    if "station_code" in columns and "passenger_count" in columns:
        return load_processed_csv(path)
    return load_turnstile_csv(path)


def import_dataset(replace: bool) -> tuple[int, int]:
    client = MongoClient(
        os.getenv("MONGODB_URI", "mongodb://127.0.0.1:27017"),
        serverSelectionTimeoutMS=3000,
    )
    database = client[os.getenv("MONGODB_DATABASE", "metroflow")]
    stations_collection = database["stations"]
    records_collection = database["passenger_records"]

    client.admin.command("ping")
    source_path = Path(os.getenv("METROFLOW_CSV_PATH", str(DEFAULT_SOURCE_PATH)))
    if not source_path.is_absolute():
        source_path = PROJECT_ROOT / source_path
    if not source_path.exists():
        raise FileNotFoundError(f"Dataset not found: {source_path}")

    stations, records = load_source_dataset(source_path)
    if not stations or not records:
        raise ValueError(f"No usable records found in {source_path}")

    if replace:
        stations_collection.delete_many({})
        records_collection.delete_many({})
    else:
        existing_record_count = records_collection.count_documents({})
        if existing_record_count:
            raise ValueError(
                "passenger_records is not empty; rerun with --replace to import again"
            )

    stations_collection.insert_many(stations)
    records_collection.insert_many(records)
    return len(stations), len(records)


def main() -> None:
    parser = argparse.ArgumentParser(description="Import the MetroFlow CSV dataset into MongoDB.")
    parser.add_argument(
        "--replace",
        action="store_true",
        help="replace existing stations and passenger records before importing",
    )
    parser.add_argument(
        "--source",
        help="CSV path relative to the project root or an absolute path; defaults to data/metroflow_processed_network.csv",
    )
    args = parser.parse_args()
    if args.source:
        os.environ["METROFLOW_CSV_PATH"] = args.source
    station_count, record_count = import_dataset(args.replace)
    print(f"Imported {station_count} stations and {record_count} passenger records.")


if __name__ == "__main__":
    main()