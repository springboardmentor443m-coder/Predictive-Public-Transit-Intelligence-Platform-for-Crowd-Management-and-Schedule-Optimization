import pandas as pd
import numpy as np
import os

CROWD_FILE = os.path.join("data", "live_crowd_summary.csv")
SCHEDULE_FILE = os.path.join("data", "frequency_recommendations.csv")
OUTPUT_FILE = os.path.join("data", "operational_telemetry.csv")

def build_telemetry_feed():
    if not os.path.exists(CROWD_FILE) or not os.path.exists(SCHEDULE_FILE):
        print("Missing prerequisite summary files. Ensure Steps 6 & 7 have run.")
        return

    crowd_df = pd.read_csv(CROWD_FILE)
    sched_df = pd.read_csv(SCHEDULE_FILE)

    records = []
    # Interleave line operational performance with station flow
    for idx, crow_row in crowd_df.iterrows():
        matched_sched = sched_df.iloc[idx % len(sched_df)]
        
        inflow = int(crow_row["inflow"])
        delay = float(matched_sched["delay_minutes"])
        headway = int(matched_sched["adjusted_headway_min"])

        # Compute Operational Health Score (0 - 100)
        # Higher inflow and higher delay degrade system health
        health_penalty = min(delay * 6.5, 45.0) + min((inflow / 2500.0) * 45.0, 45.0)
        system_health_score = max(round(100.0 - health_penalty, 1), 10.0)

        status = "NORMAL"
        if system_health_score < 50.0:
            status = "CRITICAL ACTION REQUIRED"
        elif system_health_score < 75.0:
            status = "DEGRADED FLOW"

        records.append({
            "telemetry_id": f"TEL-{1000 + idx}",
            "station_id": crow_row["station_id"],
            "assigned_route": matched_sched["route_id"],
            "current_inflow": inflow,
            "corridor_delay_min": delay,
            "active_headway_min": headway,
            "operational_health_score": system_health_score,
            "service_status": status
        })

    out_df = pd.DataFrame(records)
    out_df.to_csv(OUTPUT_FILE, index=False)
    print(f"Step 9 Complete: Operational telemetry saved to {OUTPUT_FILE}")

if __name__ == "__main__":
    build_telemetry_feed()