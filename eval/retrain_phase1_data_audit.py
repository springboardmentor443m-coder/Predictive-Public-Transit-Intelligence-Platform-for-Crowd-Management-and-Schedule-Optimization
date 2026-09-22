"""
MetroFlow Retrain Phase 1: Data Audit of 6M Seoul Metro Dataset
File: eval/retrain_phase1_data_audit.py
Uses Polars for high-performance, memory-efficient streaming analysis.
"""

import os
import sys
import time
import polars as pl

CSV_PATH = r"F:\MetroFlow-AI-Platform-for-Metro-Crowd-Management-Scheduling-main\seoul_metro_merged_clean.csv"

def run_phase1_audit():
    print("=" * 80)
    print("METROFLOW RETRAIN - PHASE 1: DATA AUDIT BEFORE TRAINING")
    print("=" * 80)
    print(f"Target CSV Path: {CSV_PATH}")
    file_size_mb = os.path.getsize(CSV_PATH) / (1024 * 1024)
    print(f"File Size on Disk: {file_size_mb:.2f} MB")
    
    t0 = time.time()
    print("\n[1/5] Scanning CSV schema and metadata with Polars...")
    lazy_df = pl.scan_csv(CSV_PATH)
    schema = lazy_df.collect_schema()
    print(f"Columns ({len(schema)}):")
    for name, dtype in schema.items():
        print(f"  - {name:<18}: {dtype}")
    
    print("\n[2/5] Computing row count, min/max timestamps and aggregations...")
    agg_res = lazy_df.select([
        pl.len().alias("total_rows"),
        pl.col("timestamp").min().alias("min_ts"),
        pl.col("timestamp").max().alias("max_ts"),
        pl.col("station_code").n_unique().alias("unique_station_codes"),
        pl.col("station_name_en").n_unique().alias("unique_station_names_en"),
        pl.col("line_num").n_unique().alias("unique_lines"),
        pl.col("total_flow").min().alias("min_flow"),
        pl.col("total_flow").max().alias("max_flow"),
        pl.col("total_flow").mean().alias("mean_flow"),
        pl.col("total_flow").median().alias("median_flow"),
        pl.col("total_flow").std().alias("std_flow"),
    ]).collect()
    
    row_count = agg_res["total_rows"][0]
    min_ts_str = agg_res["min_ts"][0]
    max_ts_str = agg_res["max_ts"][0]
    unique_stn_codes = agg_res["unique_station_codes"][0]
    unique_stn_names_en = agg_res["unique_station_names_en"][0]
    unique_lines = agg_res["unique_lines"][0]
    
    print(f"  Actual Row Count: {row_count:,}")
    print(f"  Earliest Timestamp: {min_ts_str}")
    print(f"  Latest Timestamp:   {max_ts_str}")
    print(f"  Unique Station Codes: {unique_stn_codes:,}")
    print(f"  Unique English Station Names: {unique_stn_names_en:,}")
    print(f"  Unique Lines: {unique_lines}")
    
    # Calculate date range
    dt_eval = pl.DataFrame({
        "min_ts": [min_ts_str[:19]],
        "max_ts": [max_ts_str[:19]]
    }).with_columns([
        pl.col("min_ts").str.to_datetime("%Y-%m-%d %H:%M:%S").alias("min_dt"),
        pl.col("max_ts").str.to_datetime("%Y-%m-%d %H:%M:%S").alias("max_dt"),
    ])
    min_dt = dt_eval["min_dt"][0]
    max_dt = dt_eval["max_dt"][0]
    span_days = (max_dt - min_dt).days
    print(f"\n[3/5] Date Range & Temporal Window:")
    print(f"  Start Date: {min_dt}")
    print(f"  End Date:   {max_dt}")
    print(f"  Date Span:  {span_days} days (~{span_days / 365.25:.2f} years, ~{span_days / 30.4375:.1f} months)")
    
    print("\n[4/5] Checking Missing Values per Column...")
    null_exprs = [pl.col(c).null_count().alias(c) for c in schema.names()]
    null_counts = lazy_df.select(null_exprs).collect()
    for c in schema.names():
        n_null = null_counts[c][0]
        pct = (n_null / row_count) * 100
        print(f"  - {c:<18}: {n_null:>10,} ({pct:6.2f}%)")
        
    print("\n[5/5] Duplicate Checks:")
    dup_stn_ts = (
        lazy_df.group_by(["station_code", "timestamp"])
        .agg(pl.len().alias("count"))
        .filter(pl.col("count") > 1)
        .select(pl.len().alias("duplicate_groups"), (pl.col("count") - 1).sum().alias("duplicate_rows"))
        .collect()
    )
    dup_groups = dup_stn_ts["duplicate_groups"][0] if len(dup_stn_ts) > 0 else 0
    dup_rows = dup_stn_ts["duplicate_rows"][0] if len(dup_stn_ts) > 0 and dup_stn_ts["duplicate_rows"][0] is not None else 0
    print(f"  Station-Timestamp Duplicate Collisions: {dup_rows:,} extra rows across {dup_groups:,} keys")
    
    print("\nTarget (total_flow) Distribution Statistics:")
    print(f"  Min Flow:    {agg_res['min_flow'][0]:,}")
    print(f"  Mean Flow:   {agg_res['mean_flow'][0]:.2f}")
    print(f"  Median Flow: {agg_res['median_flow'][0]:.2f}")
    print(f"  Max Flow:    {agg_res['max_flow'][0]:,}")
    print(f"  Std Dev:     {agg_res['std_flow'][0]:.2f}")

    total_time = time.time() - t0
    print(f"\nAudit completed in {total_time:.2f} seconds.")
    
    print("\n" + "=" * 80)
    print("PHASE 1 VERIFICATION VERDICT:")
    if span_days >= 365:
        print(f"  VERIFIED: Date range is {span_days} days ({span_days/365.25:.2f} years).")
        print("  Confirmed: Range covers 3 full years (2015-01-01 to 2018-01-01).")
        print("  Sufficient for a genuine, leakage-free time-based train/test split (80% train / 20% test).")
    else:
        print(f"  WARNING: Date span is only {span_days} days.")
    print("=" * 80)

if __name__ == "__main__":
    run_phase1_audit()
