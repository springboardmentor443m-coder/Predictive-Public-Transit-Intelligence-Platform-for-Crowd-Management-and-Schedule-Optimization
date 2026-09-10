"""
simulator.py - Real-Time Transit Telemetry Simulator
Generates fluctuating passenger movements, delays, and surges
to simulate live IoT sensors and turnstiles in production.
"""

import os
import random
import pandas as pd
from datetime import datetime

DATA_DIR = os.path.join(os.path.dirname(__file__), "data")
CROWD_CSV = os.path.join(DATA_DIR, "live_crowd_summary.csv")
SCHEDULE_CSV = os.path.join(DATA_DIR, "active_schedules.csv")

def simulate_realtime_tick():
    """Mutates current crowd counts and schedules to create realistic live drift."""
    # 1. Update Crowd Footfall
    if os.path.exists(CROWD_CSV):
        df = pd.read_csv(CROWD_CSV)
        for idx in range(len(df)):
            # Drift net flow up or down by a random fluctuation
            delta = random.randint(-45, 60)
            current_net = int(df.loc[idx, "net_flow"]) if "net_flow" in df.columns else 500
            new_net = max(80, current_net + delta)
            df.loc[idx, "net_flow"] = new_net
            
            # Recompute dynamic status badge based on new volume
            if new_net >= 1200:
                df.loc[idx, "congestion_level"] = "CRITICAL"
            elif new_net >= 800:
                df.loc[idx, "congestion_level"] = "HIGH"
            elif new_net >= 400:
                df.loc[idx, "congestion_level"] = "MODERATE"
            else:
                df.loc[idx, "congestion_level"] = "NORMAL"
                
        df.to_csv(CROWD_CSV, index=False)

    # 2. Update Train Delays and Headways
    if os.path.exists(SCHEDULE_CSV):
        df_sch = pd.read_csv(SCHEDULE_CSV)
        for idx in range(len(df_sch)):
            # Random delay fluctuation (-0.5 to +0.8 min)
            delay_change = round(random.uniform(-0.5, 0.8), 1)
            current_delay = float(df_sch.loc[idx, "delay_minutes"]) if "delay_minutes" in df_sch.columns else 2.0
            new_delay = max(0.0, round(current_delay + delay_change, 1))
            df_sch.loc[idx, "delay_minutes"] = new_delay
        df_sch.to_csv(SCHEDULE_CSV, index=False)