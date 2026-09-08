from datetime import datetime, timezone
from typing import Dict, Any, List
from sqlalchemy.orm import Session
from sqlalchemy import select
from fastapi import HTTPException, status
from app.models.station import Station
from app.models.train_status import TrainStatus

# Threshold boundaries for density scale (0 - 100)
LOW_CONGESTION_MAX = 40.0
MEDIUM_CONGESTION_MAX = 68.0
HIGH_CONGESTION_MAX = 86.0


def recommend_frequency(density: float, congestion_label: str) -> Dict[str, str]:
    """
    Expert rule engine that evaluates predicted platform density and returns
    explainable train headway and frequency recommendations.
    
    Threshold Ranges:
      - [0.0, 40.0):   Low       -> Maintain standard off-peak schedule
      - [40.0, 68.0):  Medium    -> Monitor; no change needed yet
      - [68.0, 86.0):  High      -> Increase frequency by 2 trains/hour
      - [86.0, 100.0]: Critical  -> Increase frequency by 4 trains/hour & flag operator
    """
    # Normalize if density is passed on 0.0 - 1.0 scale
    norm_density = density * 100.0 if density <= 1.0 else density

    if norm_density < LOW_CONGESTION_MAX:
        return {
            "recommended_action": "maintain current schedule",
            "urgency": "low",
            "reason": f"Predicted density of {norm_density:.1f}% is within normal capacity (<{LOW_CONGESTION_MAX:.0f}%).",
        }
    elif norm_density < MEDIUM_CONGESTION_MAX:
        return {
            "recommended_action": "monitor; no change needed yet",
            "urgency": "medium",
            "reason": f"Predicted density of {norm_density:.1f}% reflects moderate flow ({LOW_CONGESTION_MAX:.0f}%–{MEDIUM_CONGESTION_MAX - 0.1:.0f}%).",
        }
    elif norm_density < HIGH_CONGESTION_MAX:
        return {
            "recommended_action": "increase frequency by 2 trains/hour",
            "urgency": "high",
            "reason": f"Predicted density of {norm_density:.1f}% exceeds high-congestion threshold of {MEDIUM_CONGESTION_MAX:.0f}%.",
        }
    else:
        return {
            "recommended_action": "increase frequency by 4 trains/hour and flag for operator review",
            "urgency": "critical",
            "reason": f"Predicted density of {norm_density:.1f}% exceeds critical overcrowding threshold of {HIGH_CONGESTION_MAX:.0f}%.",
        }


def handle_delay(
    db: Session,
    line: str,
    station_code: str,
    delay_minutes: int,
    downstream_count: int = 4,
    decay_rate: float = 0.75,
) -> Dict[str, Any]:
    """
    Simulates operational delay propagation across downstream stations on the same line.
    
    1. Validates line and origin station exist.
    2. Retrieves line stations in physical track order.
    3. Computes downstream delay decay: Delay_k = Delay_0 * (decay_rate ^ k).
    4. Writes a new TrainStatus telemetry record into the database.
    5. Returns downstream impact details.
    """
    # 1. Validate station existence
    incident_station = db.execute(
        select(Station).where(Station.station_code == station_code.strip())
    ).scalar_one_or_none()

    if not incident_station:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Origin station code '{station_code}' not found in network.",
        )

    # 2. Validate station belongs to requested line
    if incident_station.line.lower() != line.strip().lower():
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Station '{incident_station.name_en}' is on {incident_station.line}, not '{line}'.",
        )

    # 3. Retrieve all stations along this line in track order
    line_stations = db.execute(
        select(Station).where(Station.line.ilike(line.strip())).order_by(Station.station_code.asc())
    ).scalars().all()

    if not line_stations:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Line '{line}' has no registered stations in database.",
        )

    # Find index of incident station in track sequence
    origin_idx = None
    for idx, st in enumerate(line_stations):
        if st.station_code == incident_station.station_code:
            origin_idx = idx
            break

    # 4. Compute downstream decay
    affected_stations: List[Dict[str, Any]] = []
    
    if origin_idx is not None:
        # Check next N stations along track
        next_stations = line_stations[origin_idx + 1 : origin_idx + 1 + downstream_count]
        
        # If origin is at the end of line, wrap around for loop lines (Line 2)
        if len(next_stations) < downstream_count and "2" in line:
            wrap_needed = downstream_count - len(next_stations)
            next_stations.extend(line_stations[:wrap_needed])

        for hop, st in enumerate(next_stations, start=1):
            propagated_delay = round(delay_minutes * (decay_rate ** hop), 1)
            affected_stations.append({
                "station_code": st.station_code,
                "name_en": st.name_en,
                "station_order": hop,
                "estimated_delay_minutes": propagated_delay,
                "estimated_eta_delay_seconds": int(propagated_delay * 60),
            })

    # 5. Record telemetry in train_status table
    now = datetime.now(timezone.utc)
    train_record = TrainStatus(
        line=incident_station.line,
        timestamp=now,
        occupancy_pct=min(100.0, 50.0 + float(delay_minutes * 3.5)),
        delay_minutes=delay_minutes,
    )
    db.add(train_record)
    db.commit()

    return {
        "line": incident_station.line,
        "incident_station_code": incident_station.station_code,
        "incident_station_name": incident_station.name_en,
        "initial_delay_minutes": delay_minutes,
        "logged_at": now,
        "affected_stations": affected_stations,
    }
