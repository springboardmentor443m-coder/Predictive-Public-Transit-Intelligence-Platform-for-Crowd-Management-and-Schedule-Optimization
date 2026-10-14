from fastapi import APIRouter
from datetime import datetime
import random

router = APIRouter(prefix="/api/crowd", tags=["Crowd Intelligence"])

@router.get("/live-telemetry")
def get_live_crowd_telemetry():
    stations_data = [
        {
            "station_id": "ST-01",
            "name": "Central Terminal",
            "line": "Blue Corridor",
            "entry_turnstiles_active": 12,
            "exit_turnstiles_active": 10,
            "inflow_per_min": 215,
            "outflow_per_min": 140,
            "current_platform_load_pct": 76,
            "trend": "INCREASING",
            "crowd_status": "ELEVATED"
        },
        {
            "station_id": "ST-02",
            "name": "Tech Hub Junction",
            "line": "Interchange",
            "entry_turnstiles_active": 18,
            "exit_turnstiles_active": 16,
            "inflow_per_min": 340,
            "outflow_per_min": 290,
            "current_platform_load_pct": 89,
            "trend": "SURGE",
            "crowd_status": "CRITICAL"
        },
        {
            "station_id": "ST-03",
            "name": "Cyber Gateway",
            "line": "Interchange",
            "entry_turnstiles_active": 10,
            "exit_turnstiles_active": 8,
            "inflow_per_min": 130,
            "outflow_per_min": 115,
            "current_platform_load_pct": 58,
            "trend": "STABLE",
            "crowd_status": "NORMAL"
        },
        {
            "station_id": "ST-04",
            "name": "Financial District",
            "line": "Blue Corridor",
            "entry_turnstiles_active": 14,
            "exit_turnstiles_active": 12,
            "inflow_per_min": 280,
            "outflow_per_min": 210,
            "current_platform_load_pct": 83,
            "trend": "INCREASING",
            "crowd_status": "CRITICAL"
        },
        {
            "station_id": "ST-05",
            "name": "South Port",
            "line": "Emerald Express",
            "entry_turnstiles_active": 8,
            "exit_turnstiles_active": 6,
            "inflow_per_min": 75,
            "outflow_per_min": 85,
            "current_platform_load_pct": 41,
            "trend": "DECREASING",
            "crowd_status": "NORMAL"
        },
        {
            "station_id": "ST-06",
            "name": "Market Square",
            "line": "Emerald Express",
            "entry_turnstiles_active": 10,
            "exit_turnstiles_active": 8,
            "inflow_per_min": 125,
            "outflow_per_min": 110,
            "current_platform_load_pct": 52,
            "trend": "STABLE",
            "crowd_status": "NORMAL"
        }
    ]

    return {
        "timestamp": datetime.utcnow().isoformat(),
        "total_active_turnstiles": sum(s["entry_turnstiles_active"] + s["exit_turnstiles_active"] for s in stations_data),
        "network_net_inflow_per_min": sum(s["inflow_per_min"] - s["outflow_per_min"] for s in stations_data),
        "crowd_telemetry": stations_data
    }