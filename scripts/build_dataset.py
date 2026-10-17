"""
MetroFlow Data Pipeline Builder
================================
Rebuilds the clean master dataset for NYC MTA Subway Hourly Ridership (2022-2024)
focused on the Top 12 Station Complexes.

Outputs:
  - metroflow/data/raw/ (cached raw downloads)
  - metroflow/data/top_12_stations.csv
  - metroflow/data/station_metadata.csv
  - metroflow/data/incidents_summary.csv
  - metroflow/data/data_quality_report.csv
  - metroflow/data/processed/metroflow_master.csv
  - metroflow/data/metroflow_master.csv
"""

import os
import sys
import time
import requests
import pandas as pd
import numpy as np

# Root path setup
SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))
PROJECT_ROOT = os.path.abspath(os.path.join(SCRIPT_DIR, ".."))
DATA_DIR = os.path.join(PROJECT_ROOT, "data")
RAW_DIR = os.path.join(DATA_DIR, "raw")
PROCESSED_DIR = os.path.join(DATA_DIR, "processed")

os.makedirs(RAW_DIR, exist_ok=True)
os.makedirs(PROCESSED_DIR, exist_ok=True)

SODA_RIDERSHIP_URL = "https://data.ny.gov/resource/wujg-7c2s.json"
SODA_STATIONS_URL = "https://data.ny.gov/resource/39hk-dx4f.json"
SODA_INCIDENTS_URL = "https://data.ny.gov/resource/g937-7k7c.json"

def log(msg):
    print(msg, flush=True)

def fetch_top_12_stations():
    """Identifies top 12 stations by sampling total ridership across 2022-2024."""
    top_file = os.path.join(DATA_DIR, "top_12_stations.csv")
    if os.path.exists(top_file):
        log(f"[CACHE] Loading top 12 stations from {top_file}")
        top_df = pd.read_csv(top_file)
        top_df['station_complex_id'] = top_df['station_complex_id'].astype(str)
        return top_df

    log("[FETCH] Ranking stations by total ridership (2022-2024)...")
    sample_periods = [
        ("2022-05-01T00:00:00.000", "2022-05-07T23:59:59.999"),
        ("2023-05-01T00:00:00.000", "2023-05-07T23:59:59.999"),
        ("2024-05-01T00:00:00.000", "2024-05-07T23:59:59.999")
    ]
    all_data = []
    for start, end in sample_periods:
        params = {
            "$select": "station_complex_id, station_complex, ridership",
            "$where": f"transit_timestamp >= '{start}' AND transit_timestamp <= '{end}'",
            "$limit": 50000
        }
        r = requests.get(SODA_RIDERSHIP_URL, params=params, timeout=30)
        if r.status_code == 200:
            all_data.extend(r.json())
        else:
            raise RuntimeError(f"Failed to fetch sample ridership data: {r.status_code} {r.text}")

    df_sample = pd.DataFrame(all_data)
    df_sample['ridership'] = pd.to_numeric(df_sample['ridership'], errors='coerce').fillna(0)
    df_sample['station_complex_id'] = df_sample['station_complex_id'].astype(str)
    
    grouped = df_sample.groupby(['station_complex_id', 'station_complex'])['ridership'].sum().reset_index()
    grouped = grouped.sort_values(by='ridership', ascending=False).reset_index(drop=True)
    
    top_12 = grouped.head(12).copy()
    top_12['rank'] = range(1, 13)
    top_12 = top_12.rename(columns={'ridership': 'total_ridership'})
    top_12 = top_12[['rank', 'station_complex_id', 'station_complex', 'total_ridership']]
    
    top_12.to_csv(top_file, index=False)
    log(f"[SAVED] {top_file}")
    return top_12

def fetch_hourly_ridership(top_ids):
    """Retrieves and caches hourly ridership for the 12 target stations (2022-2024)."""
    raw_ridership_file = os.path.join(RAW_DIR, "raw_ridership_top12.csv")
    if os.path.exists(raw_ridership_file):
        log(f"[CACHE] Loading raw ridership from {raw_ridership_file}")
        df = pd.read_csv(raw_ridership_file, dtype={'station_complex_id': str})
        return df

    log("[FETCH] Retrieving hourly ridership data for top 12 stations (2022-2024)...")
    ids_str = ",".join([f"'{i}'" for i in top_ids])
    
    chunks = [
        ("2022-01-01T00:00:00.000", "2022-03-31T23:59:59.999"),
        ("2022-04-01T00:00:00.000", "2022-06-30T23:59:59.999"),
        ("2022-07-01T00:00:00.000", "2022-09-30T23:59:59.999"),
        ("2022-10-01T00:00:00.000", "2022-12-31T23:59:59.999"),
        ("2023-01-01T00:00:00.000", "2023-03-31T23:59:59.999"),
        ("2023-04-01T00:00:00.000", "2023-06-30T23:59:59.999"),
        ("2023-07-01T00:00:00.000", "2023-09-30T23:59:59.999"),
        ("2023-10-01T00:00:00.000", "2023-12-31T23:59:59.999"),
        ("2024-01-01T00:00:00.000", "2024-03-31T23:59:59.999"),
        ("2024-04-01T00:00:00.000", "2024-06-30T23:59:59.999"),
        ("2024-07-01T00:00:00.000", "2024-09-30T23:59:59.999"),
        ("2024-10-01T00:00:00.000", "2024-12-31T23:59:59.999"),
    ]
    all_rows = []
    
    for start_str, end_str in chunks:
        log(f"  Downloading chunk {start_str[:10]} to {end_str[:10]}...")
        offset = 0
        limit = 50000
        while True:
            params = {
                "$select": "transit_timestamp, station_complex_id, station_complex, borough, ridership, transfers, latitude, longitude",
                "$where": f"station_complex_id IN ({ids_str}) AND transit_timestamp >= '{start_str}' AND transit_timestamp <= '{end_str}'",
                "$limit": limit,
                "$offset": offset
            }
            r = requests.get(SODA_RIDERSHIP_URL, params=params, timeout=30)
            if r.status_code == 200:
                data = r.json()
                if not data:
                    break
                all_rows.extend(data)
                offset += len(data)
                if len(data) < limit:
                    break
            else:
                log(f"Warning: HTTP {r.status_code} for {start_str}")
                break

    df_raw = pd.DataFrame(all_rows)
    df_raw['station_complex_id'] = df_raw['station_complex_id'].astype(str)
    df_raw.to_csv(raw_ridership_file, index=False)
    log(f"[SAVED] {raw_ridership_file} ({len(df_raw)} records)")
    return df_raw

def fetch_station_metadata(top_ids):
    """Fetches and prepares station metadata."""
    raw_meta_file = os.path.join(RAW_DIR, "raw_stations_metadata.csv")
    meta_output_file = os.path.join(DATA_DIR, "station_metadata.csv")
    
    if os.path.exists(meta_output_file):
        log(f"[CACHE] Loading station metadata from {meta_output_file}")
        meta_df = pd.read_csv(meta_output_file, dtype={'station_complex_id': str})
        meta_df['station_complex_id'] = meta_df['station_complex_id'].astype(str)
        return meta_df
        
    log("[FETCH] Retrieving MTA station metadata...")
    r = requests.get(f"{SODA_STATIONS_URL}?$limit=5000", timeout=20)
    if r.status_code == 200:
        df_meta = pd.DataFrame(r.json())
        df_meta.to_csv(raw_meta_file, index=False)
    else:
        raise RuntimeError("Failed to fetch MTA station metadata.")
        
    df_meta['complex_id'] = df_meta['complex_id'].astype(str)
    df_top_meta = df_meta[df_meta['complex_id'].isin(top_ids)].copy()
    
    def agg_routes(series):
        routes = set()
        for item in series.dropna():
            for r in str(item).split():
                routes.add(r)
        return " ".join(sorted(routes))

    grouped_meta = df_top_meta.groupby('complex_id').agg({
        'stop_name': lambda x: ' / '.join(sorted(set(x))),
        'line': lambda x: ' / '.join(sorted(set(x))),
        'daytime_routes': agg_routes,
        'structure': 'first',
        'ada': lambda x: 1 if any(str(v) == '1' for v in x) else 0,
    }).reset_index()
    
    grouped_meta = grouped_meta.rename(columns={
        'complex_id': 'station_complex_id',
        'daytime_routes': 'routes'
    })
    grouped_meta['station_complex_id'] = grouped_meta['station_complex_id'].astype(str)
    
    grouped_meta.to_csv(meta_output_file, index=False)
    log(f"[SAVED] {meta_output_file}")
    return grouped_meta

def fetch_incidents():
    """Fetches and saves contextual delay-causing incident data."""
    raw_incidents_file = os.path.join(RAW_DIR, "raw_incidents.csv")
    incidents_output_file = os.path.join(DATA_DIR, "incidents_summary.csv")
    
    if os.path.exists(incidents_output_file):
        log(f"[CACHE] Loading incidents summary from {incidents_output_file}")
        return pd.read_csv(incidents_output_file)

    log("[FETCH] Retrieving MTA incident dataset...")
    r = requests.get(f"{SODA_INCIDENTS_URL}?$limit=50000", timeout=20)
    if r.status_code == 200:
        df_inc = pd.DataFrame(r.json())
        df_inc.to_csv(raw_incidents_file, index=False)
    else:
        log("Warning: Incidents dataset download failed. Proceeding without incidents.")
        return None

    df_inc['incidents'] = pd.to_numeric(df_inc['incidents'], errors='coerce').fillna(0)
    inc_summary = df_inc.groupby(['month', 'line', 'reporting_category'])['incidents'].sum().reset_index()
    inc_summary = inc_summary.sort_values(by=['month', 'incidents'], ascending=[True, False])
    inc_summary.to_csv(incidents_output_file, index=False)
    log(f"[SAVED] {incidents_output_file}")
    return inc_summary

def process_and_validate():
    """Main pipeline execution & validation."""
    log("=" * 60)
    log("STARTING METROFLOW DATASET PIPELINE")
    log("=" * 60)
    
    # 1. Target Station Selection
    df_top12 = fetch_top_12_stations()
    top_ids = [str(x) for x in df_top12['station_complex_id'].unique()]
    
    # 2. Hourly Ridership Fetch
    df_raw = fetch_hourly_ridership(top_ids)
    
    log("[PROCESS] Cleaning and aggregating raw ridership data...")
    # Data Cleaning & Aggregation
    df_raw['station_complex_id'] = df_raw['station_complex_id'].astype(str)
    df_raw['ridership'] = pd.to_numeric(df_raw['ridership'], errors='coerce').fillna(0)
    df_raw['transfers'] = pd.to_numeric(df_raw['transfers'], errors='coerce').fillna(0)
    df_raw['latitude'] = pd.to_numeric(df_raw['latitude'], errors='coerce')
    df_raw['longitude'] = pd.to_numeric(df_raw['longitude'], errors='coerce')
    
    # Parse transit_timestamp
    df_raw['transit_timestamp'] = pd.to_datetime(df_raw['transit_timestamp'])
    
    # Filter strict date range 2022-01-01 to 2024-12-31
    mask = (df_raw['transit_timestamp'] >= '2022-01-01') & (df_raw['transit_timestamp'] <= '2024-12-31 23:59:59')
    df_filtered = df_raw[mask].copy()
    
    # Aggregate multiple payment methods per station-hour
    agg_df = df_filtered.groupby(['transit_timestamp', 'station_complex_id', 'station_complex', 'borough']).agg({
        'ridership': 'sum',
        'transfers': 'sum',
        'latitude': 'first',
        'longitude': 'first'
    }).reset_index()
    
    agg_df = agg_df.rename(columns={
        'ridership': 'passenger_count'
    })
    
    agg_df['station_complex_id'] = agg_df['station_complex_id'].astype(str)
    
    # Sort chronologically by station and timestamp
    agg_df = agg_df.sort_values(by=['station_complex_id', 'transit_timestamp']).reset_index(drop=True)
    
    # Remove exact duplicate station/timestamp combinations if any
    agg_df = agg_df.drop_duplicates(subset=['station_complex_id', 'transit_timestamp']).reset_index(drop=True)
    
    # 3. Station Metadata Join
    df_meta = fetch_station_metadata(top_ids)
    df_meta['station_complex_id'] = df_meta['station_complex_id'].astype(str)
    
    master_df = pd.merge(agg_df, df_meta[['station_complex_id', 'routes', 'structure', 'ada', 'line']], 
                         on='station_complex_id', how='left')
                         
    # 4. Contextual Incidents
    fetch_incidents()
    
    # 5. Hourly Continuity Check & Quality Report
    log("[PROCESS] Computing hourly continuity and data quality report...")
    quality_rows = []
    full_hourly_range = pd.date_range(start='2022-01-01 00:00:00', end='2024-12-31 23:00:00', freq='h')
    expected_hours = len(full_hourly_range)
    
    max_time_gap = pd.Timedelta(seconds=0)
    
    for st_id in top_ids:
        st_data = master_df[master_df['station_complex_id'] == st_id].copy()
        st_name = st_data['station_complex'].iloc[0] if len(st_data) > 0 else f"Station {st_id}"
        total_rows = len(st_data)
        
        # Check gaps
        st_timestamps = set(st_data['transit_timestamp'])
        missing_count = expected_hours - len(st_timestamps)
        
        # Duplicate check
        dup_count = st_data.duplicated(subset=['transit_timestamp']).sum()
        
        # Calculate largest time gap
        if len(st_data) > 1:
            diffs = st_data['transit_timestamp'].diff()
            largest_gap = diffs.max()
            if largest_gap > max_time_gap:
                max_time_gap = largest_gap
        else:
            largest_gap = pd.Timedelta(seconds=0)
            
        quality_rows.append({
            'station_complex_id': st_id,
            'station_complex': st_name,
            'total_rows': total_rows,
            'expected_hourly_rows': expected_hours,
            'missing_hourly_timestamps': missing_count,
            'duplicate_timestamps': dup_count,
            'largest_time_gap': str(largest_gap)
        })
        
    df_quality = pd.DataFrame(quality_rows)
    quality_report_file = os.path.join(DATA_DIR, "data_quality_report.csv")
    df_quality.to_csv(quality_report_file, index=False)
    log(f"[SAVED] {quality_report_file}")
    
    # Save master dataset
    processed_master_file = os.path.join(PROCESSED_DIR, "metroflow_master.csv")
    root_master_file = os.path.join(DATA_DIR, "metroflow_master.csv")
    
    master_df.to_csv(processed_master_file, index=False)
    master_df.to_csv(root_master_file, index=False)
    log(f"[SAVED] {processed_master_file}")
    log(f"[SAVED] {root_master_file}")
    
    # 6. Validation Output
    log("\n" + "=" * 40)
    log("METROFLOW DATASET COMPLETE")
    log("=" * 40)
    log(f"Rows: {len(master_df):,}")
    log(f"Stations: {master_df['station_complex_id'].nunique()}")
    log(f"Date range: {master_df['transit_timestamp'].min()} to {master_df['transit_timestamp'].max()}")
    log(f"Columns: {master_df.columns.tolist()}")
    
    log("\nStation distribution:")
    st_dist = master_df.groupby(['station_complex_id', 'station_complex']).size().reset_index(name='row_count')
    log(st_dist.to_string(index=False))
    
    log("\nMissing values:")
    log(master_df.isnull().sum().to_string())
    
    total_dups = master_df.duplicated(subset=['station_complex_id', 'transit_timestamp']).sum()
    log(f"\nDuplicate rows: {total_dups}")
    log(f"Largest time gap: {max_time_gap}")
    
    # Assertions
    assert master_df['station_complex_id'].nunique() == 12, "Should have exactly 12 stations"
    assert (master_df['passenger_count'] < 0).sum() == 0, "No negative passenger counts allowed"
    assert 'target_next_hour' not in master_df.columns, "target_next_hour should NOT be created yet"
    assert total_dups == 0, "No duplicate station/timestamp combinations allowed"
    
    quality_status = "PASS" if total_dups == 0 and (master_df['passenger_count'] < 0).sum() == 0 else "WARNING"
    log(f"\nData quality: {quality_status}")
    
    log("\n--- FIRST 10 ROWS ---")
    log(master_df.head(10).to_string(index=False))
    
    log("\n--- LAST 10 ROWS ---")
    log(master_df.tail(10).to_string(index=False))

if __name__ == "__main__":
    process_and_validate()
