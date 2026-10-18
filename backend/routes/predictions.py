"""
MetroFlow AI Prediction & Demand Forecasting Module
Exposes multi-horizon predictions (+15m, +30m, +1h, +2h), station-specific forecasts,
passenger demand projections, and smart operational headway recommendations.
"""

from fastapi import APIRouter, HTTPException, Query
from typing import Dict, Any, List
from ml.forecasting_engine import forecaster
from simulator.live_engine import simulator

router = APIRouter(prefix="/api/predictions", tags=["AI Predictions"])

@router.get("/station/{station_id}")
def get_station_multi_horizon(station_id: str):
    """
    Returns crowd density, passenger volume, and inflow/outflow forecast
    for 0m (live), +15m, +30m, +1h, and +2h horizons.
    """
    station = simulator.stations_data.get(station_id)
    if not station:
        raise HTTPException(status_code=404, detail="Station not found")

    current_occ_pct = station["density_percent"]
    forecast = forecaster.get_multi_horizon_forecast(station_id, current_occupancy_override=current_occ_pct)
    return forecast

@router.get("/horizon/{minutes}")
def get_network_horizon_predictions(minutes: int):
    """
    Returns network-wide station predictions at a target forecast horizon (+15, +30, +60, +120 mins).
    Used for predictive heatmap switching on the interactive map.
    """
    if minutes not in [0, 15, 30, 60, 120]:
        minutes = 15 # default fallback

    # Pass live current occupancy overrides
    current_states = {sid: s["density_percent"] for sid, s in simulator.stations_data.items()}
    predictions = forecaster.get_network_wide_predictions(minutes_ahead=minutes, current_station_states=current_states)

    severe_count = sum(1 for p in predictions if p["congestion_level"] == "Severe")
    high_count = sum(1 for p in predictions if p["congestion_level"] == "High")
    avg_predicted_density = round(sum(p["predicted_density_percent"] for p in predictions) / len(predictions), 1)

    return {
        "horizon_minutes": minutes,
        "horizon_label": "Live Now" if minutes == 0 else f"+{minutes} min",
        "average_network_density": avg_predicted_density,
        "critical_stations_count": severe_count + high_count,
        "stations": predictions
    }

@router.get("/recommendations")
def get_smart_recommendations():
    """
    Generates centralized smart scheduling and crowd mitigation recommendations
    by synthesizing current real-time state and +15m / +30m AI predictions.
    """
    current_states = {sid: s["density_percent"] for sid, s in simulator.stations_data.items()}
    predictions_15m = forecaster.get_network_wide_predictions(minutes_ahead=15, current_station_states=current_states)
    predictions_30m = forecaster.get_network_wide_predictions(minutes_ahead=30, current_station_states=current_states)

    top_urgent = [p for p in predictions_15m if p["predicted_density_percent"] >= 70]
    recommendation_cards = []

    for item in top_urgent[:4]:
        recommendation_cards.append({
            "station_id": item["station_id"],
            "station_name": item["station_name"],
            "borough": item["borough"],
            "current_density": round(simulator.stations_data[item["station_id"]]["density_percent"], 1),
            "projected_density_15m": item["predicted_density_percent"],
            "risk_level": item["congestion_level"],
            "recommended_headway": item["recommended_headway_mins"],
            "recommended_actions": item["recommendations"]
        })

    return {
        "status": "Active Advisory",
        "actionable_bottlenecks": len(recommendation_cards),
        "recommendations": recommendation_cards
    }
