import os
import pandas as pd
from pymongo import MongoClient

# MongoDB configuration
MONGO_URL = os.getenv("MONGO_URL", "mongodb://localhost:27017")
DB_NAME = "metroflow_db"

# Kotha dataset path
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
CSV_PATH = os.path.join(BASE_DIR, "..", "ml", "data", "metroflow_processed_network.csv")

def seed_database():
    print(f"[*] Connecting to MongoDB at: {MONGO_URL}...")
    try:
        client = MongoClient(MONGO_URL, serverSelectionTimeoutMS=5000)
        client.server_info()
        print("[+] Successfully connected to MongoDB server!")
    except Exception as e:
        print(f"[!] MongoDB Connection Failed: {e}")
        return

    db = client[DB_NAME]
    logs_col = db["turnstile_logs"]

    print(f"[*] Checking dataset at: {CSV_PATH}")
    if not os.path.exists(CSV_PATH):
        print(f"[!] File not found at: {CSV_PATH}")
        print("[!] Make sure 'metroflow_processed_network.csv' is placed inside 'backend/ml/data/'")
        return

    print("[*] Reading 'metroflow_processed_network.csv'...")
    df = pd.read_csv(CSV_PATH)

    # Dashboard UI rates & telemetry
    df['inflow_per_min'] = (df['entries'] / 60.0).round().astype(int)
    df['outflow_per_min'] = (df['exits'] / 60.0).round().astype(int)
    df['density_pct'] = (df['occupancy_rate'] * 100).round().astype(int)

    records = df.to_dict(orient="records")

    print("[*] Dropping old records from 'turnstile_logs'...")
    logs_col.drop()

    print(f"[*] Seeding {len(records):,} fresh records into MongoDB...")
    logs_col.insert_many(records)

    print("\n" + "=" * 55)
    print("      MongoDB Seeding Completed Successfully!")
    print(f"      Database   : {DB_NAME}")
    print(f"      Collection : turnstile_logs")
    print(f"      Inserted   : {len(records):,} documents")
    print("=" * 55 + "\n")

if __name__ == "__main__":
    seed_database()