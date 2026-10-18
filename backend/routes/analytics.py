"""
MetroFlow Analytics & Performance Reporting Module
Provides passenger traffic analytics, 24-hour demand curves,
station throughput summaries, and operational audit trail.
"""

from fastapi import APIRouter
from typing import Dict, Any, List
import math
from simulator.live_engine import simulator
from data.nyc_subway_data import NYC_STATIONS
from db.database import get_db_connection

router = APIRouter(prefix="/api/analytics", tags=["Analytics & Reporting"])

@router.get("/overview")
def get_analytics_overview():
    """System-level operational metrics, passenger volume trends, and safety ratings."""
    snapshot = simulator.get_full_snapshot()
    stations = snapshot["stations"]

    total_ridership_today = sum(s["current_occupancy"] * 4 for s in stations) # estimated daily cumulative
    avg_dwell_time = 32.4 # seconds
    on_time_performance = 94.8 # percent
    headway_compliance = 97.2 # percent

    return {
        "daily_ridership_estimated": total_ridership_today,
        "on_time_performance_percent": on_time_performance,
        "headway_compliance_percent": headway_compliance,
        "avg_station_dwell_seconds": avg_dwell_time,
        "active_corridor_efficiency": "Optimal",
        "turnstile_throughput_total_hourly": sum(s["inflow_rate"] * 12 for s in stations),
        "busiest_borough": "Manhattan",
        "network_state": snapshot["network_metrics"]
    }

@router.get("/hourly-patterns")
def get_24hr_demand_patterns():
    """Returns 24-hour baseline vs peak-day passenger demand curve for transit planning."""
    hourly_data = []
    
    # Generate 24 hours of realistic NYC transit volume
    for h in range(24):
        # Commuter peaks at 8 and 18
        morning = math.exp(-((h - 8.2) ** 2) / 1.8) * 125000
        evening = math.exp(-((h - 17.5) ** 2) / 2.2) * 142000
        midday = math.exp(-((h - 13.0) ** 2) / 4.0) * 45000
        base = 18000 if (h < 5 or h > 23) else 42000

        actual_ridership = int(base + morning + evening + midday)
        forecast_ridership = int(actual_ridership * 1.02)
        train_capacity_offered = int(max(actual_ridership * 1.15, 50000))

        hourly_data.append({
            "hour": f"{h:02d}:00",
            "hour_num": h,
            "actual_passengers": actual_ridership,
            "forecast_passengers": forecast_ridership,
            "train_capacity_offered": train_capacity_offered,
            "is_peak": (7 <= h <= 9) or (16 <= h <= 19)
        })

    return {"demand_curve": hourly_data}

@router.get("/station-rankings")
def get_station_performance_rankings():
    """Ranks stations by ridership density, turnstile volume, and congestion index."""
    stations = list(simulator.stations_data.values())
    ranked = sorted(stations, key=lambda s: s["density_percent"], reverse=True)
    return {
        "rankings": [
            {
                "rank": idx + 1,
                "id": s["id"],
                "name": s["name"],
                "borough": s["borough"],
                "density_percent": s["density_percent"],
                "inflow_rate": s["inflow_rate"],
                "outflow_rate": s["outflow_rate"],
                "congestion_level": s["congestion_level"],
                "capacity": s["capacity"]
            }
            for idx, s in enumerate(ranked)
        ]
    }

@router.get("/audit-logs")
def get_audit_logs():
    """Returns operational change logs taken by admins and rail dispatchers."""
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute("""
    SELECT id, user_name, role, action, details, timestamp
    FROM operational_logs
    ORDER BY id DESC
    LIMIT 25
    """)
    logs = [dict(r) for r in cursor.fetchall()]
    conn.close()
    return {"logs": logs}
