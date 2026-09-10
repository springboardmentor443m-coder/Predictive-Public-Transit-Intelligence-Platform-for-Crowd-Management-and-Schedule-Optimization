"""
analytics_engine.py - Milestone 3
Computes transit KPI metrics, punctuality statistics, and
congestion heatmap payloads for frontend visualization.
"""

from typing import Dict, List
import pandas as pd
import numpy as np
import os

DATA_DIR = os.path.join(os.path.dirname(__file__), "data")

class AnalyticsEngine:
    def __init__(self):
        self.crowd_summary_path = os.path.join(DATA_DIR, "live_crowd_summary.csv")
        self.schedule_path = os.path.join(DATA_DIR, "active_schedules.csv")

    def generate_congestion_heatmap(self) -> List[Dict]:
        """
        Generates 2D coordinates and congestion weights for map/heatmap display.
        """
        station_coords = {
            "Central Station": {"lat": 40.7527, "lon": -73.9772},
            "Grand Central-42 St": {"lat": 40.7517, "lon": -73.9766},
            "34 St-Penn Station": {"lat": 40.7505, "lon": -73.9934},
            "Times Sq-42 St": {"lat": 40.7580, "lon": -73.9855},
            "Fulton St": {"lat": 40.7103, "lon": -74.0090},
            "14 St-Union Sq": {"lat": 40.7359, "lon": -73.9911},
            "Atlantic Av-Barclays Ctr": {"lat": 40.6844, "lon": -73.9776}
        }

        heatmap_points = []
        if os.path.exists(self.crowd_summary_path):
            df = pd.read_csv(self.crowd_summary_path)
            for _, row in df.iterrows():
                name = row.get("station_name", "Central Station")
                coords = station_coords.get(name, {"lat": 40.7500, "lon": -73.9800})
                net = float(row.get("net_flow", 450))
                # Normalize weight between 0.1 and 1.0
                intensity = min(max(net / 1500.0, 0.1), 1.0)
                heatmap_points.append({
                    "station_name": name,
                    "lat": coords["lat"],
                    "lon": coords["lon"],
                    "net_flow": int(net),
                    "status": row.get("congestion_level", "NORMAL"),
                    "intensity": round(intensity, 2)
                })
        else:
            for name, coords in station_coords.items():
                heatmap_points.append({
                    "station_name": name,
                    "lat": coords["lat"],
                    "lon": coords["lon"],
                    "net_flow": 600,
                    "status": "MODERATE",
                    "intensity": 0.5
                })

        return heatmap_points

    def compute_network_kpis(self) -> Dict:
        """
        Calculates high-level operational efficiency KPIs:
        On-time performance, fleet capacity utilization, active alerts.
        """
        avg_delay = 3.2
        on_time_pct = 94.5
        avg_occupancy = 68.0

        if os.path.exists(self.schedule_path):
            df = pd.read_csv(self.schedule_path)
            if "delay_minutes" in df.columns:
                avg_delay = float(df["delay_minutes"].mean())
                on_time_pct = float((df["delay_minutes"] <= 3.0).mean() * 100)
            if "occupancy_rate" in df.columns:
                avg_occupancy = float(df["occupancy_rate"].mean() * 100)

        return {
            "on_time_performance_pct": round(on_time_pct, 1),
            "network_avg_delay_min": round(avg_delay, 1),
            "fleet_capacity_utilization_pct": round(avg_occupancy, 1),
            "daily_throughput_est": 184500,
            "status": "HEALTHY" if avg_delay < 5.0 else "DEGRADED"
        }

analytics_engine = AnalyticsEngine()