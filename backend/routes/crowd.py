"""
MetroFlow Crowd Monitoring Module
Real-time passenger density tracking, crowd heatmap data generation,
congestion classification, and station turnstile inflow/outflow feeds.
"""

from fastapi import APIRouter, HTTPException
from typing import Dict, Any, List
from simulator.live_engine import simulator
from data.nyc_subway_data import NYC_STATIONS

router = APIRouter(prefix="/api/crowd", tags=["Crowd Monitoring"])

@router.get("/live")
def get_live_crowd_snapshot():
    """Returns network-wide real-time passenger density, active trains, and congestion status."""
    return simulator.get_full_snapshot()

@router.get("/heatmap")
def get_crowd_heatmap():
    """
    Returns geospatial coordinates and crowd intensity weights (0.0 to 1.0)
    for interactive NYC subway map heatmap rendering.
    """
    snapshot = simulator.get_full_snapshot()
    heatmap_points = []

    for s in snapshot["stations"]:
        # Normalized weight between 0.2 and 1.0 based on density
        weight = max(0.15, min(1.0, round(s["density_percent"] / 100.0, 2)))
        heatmap_points.append({
            "station_id": s["id"],
            "name": s["name"],
            "borough": s["borough"],
            "lat": s["lat"],
            "lon": s["lon"],
            "lines": s["lines"],
            "current_occupancy": s["current_occupancy"],
            "capacity": s["capacity"],
            "density_percent": s["density_percent"],
            "congestion_level": s["congestion_level"],
            "weight": weight
        })

    return {
        "timestamp": snapshot["timestamp"],
        "count": len(heatmap_points),
        "heatmap_points": heatmap_points
    }

@router.get("/station/{station_id}")
def get_station_crowd_details(station_id: str):
    """Detailed station analytics, turnstile sensor data, and 12-minute historical trend."""
    station = simulator.stations_data.get(station_id)
    if not station:
        raise HTTPException(status_code=404, detail="Station not found")

    history = simulator.history_samples.get(station_id, [])

    return {
        "station": station,
        "history": history,
        "sensor_telemetry": {
            "turnstiles_operational": station["turnstiles_active"],
            "turnstiles_total": station["turnstiles"],
            "sensor_latency_ms": 42,
            "flow_efficiency_percent": 98.4,
            "dwell_clearance_rate": "8.4 sec/passenger"
        }
    }

@router.get("/flow-analysis")
def get_network_flow_analysis():
    """Station-wise comparison of inflow vs outflow rates and throughput rankings."""
    stations = list(simulator.stations_data.values())
    
    # Sort top 5 busiest entry stations and exit stations
    top_entries = sorted(stations, key=lambda x: x["inflow_rate"], reverse=True)[:5]
    top_exits = sorted(stations, key=lambda x: x["outflow_rate"], reverse=True)[:5]
    top_crowded = sorted(stations, key=lambda x: x["density_percent"], reverse=True)[:5]

    return {
        "top_inflow_stations": [
            {"id": s["id"], "name": s["name"], "borough": s["borough"], "inflow_rate": s["inflow_rate"]}
            for s in top_entries
        ],
        "top_outflow_stations": [
            {"id": s["id"], "name": s["name"], "borough": s["borough"], "outflow_rate": s["outflow_rate"]}
            for s in top_exits
        ],
        "highest_density_stations": [
            {"id": s["id"], "name": s["name"], "density_percent": s["density_percent"], "congestion_level": s["congestion_level"]}
            for s in top_crowded
        ]
    }
