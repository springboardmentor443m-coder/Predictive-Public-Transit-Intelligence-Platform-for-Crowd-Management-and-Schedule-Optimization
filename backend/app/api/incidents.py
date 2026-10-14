from fastapi import APIRouter
from pydantic import BaseModel
from datetime import datetime
from typing import List

router = APIRouter(prefix="/api/incidents", tags=["Incident Management"])

class ProtocolActionRequest(BaseModel):
    incident_id: str
    station_id: str
    action_type: str  # e.g., "GATE_METERING", "SURGE_DIVERSION", "PLATFORM_HOLD"

# Active incident store
ACTIVE_INCIDENTS = [
    {
        "id": "INC-882",
        "station_id": "ST-02",
        "station_name": "Tech Hub Junction",
        "severity": "CRITICAL",
        "type": "CROWD_SURGE_THRESHOLD_EXCEEDED",
        "density_pct": 89,
        "recommended_action": "RESTRICT_INFLOW_METERING",
        "status": "UNRESOLVED",
        "timestamp": "18:42:10"
    },
    {
        "id": "INC-883",
        "station_id": "ST-04",
        "station_name": "Financial District",
        "severity": "HIGH",
        "type": "PLATFORM_BOTTLENECK",
        "density_pct": 82,
        "recommended_action": "DEPLOY_EXTRA_HEADWAY_DISPATCH",
        "status": "UNRESOLVED",
        "timestamp": "18:47:35"
    }
]

AUDIT_LOGS = [
    {
        "log_id": "LOG-101",
        "timestamp": "18:35:00",
        "station_name": "Central Terminal",
        "action_taken": "Automated Headway Shortened to 3.0m",
        "operator": "AUTONOMOUS_ENGINE"
    }
]

@router.get("/active")
def get_active_incidents():
    return {
        "active_incidents": ACTIVE_INCIDENTS,
        "audit_logs": AUDIT_LOGS
    }

@router.post("/execute-protocol")
def execute_protocol(payload: ProtocolActionRequest):
    timestamp_now = datetime.utcnow().strftime("%H:%M:%S")
    
    # Mark incident resolved or mitigated
    for inc in ACTIVE_INCIDENTS:
        if inc["id"] == payload.incident_id:
            inc["status"] = "MITIGATED"

    # Add entry to audit logs
    AUDIT_LOGS.insert(0, {
        "log_id": f"LOG-{len(AUDIT_LOGS) + 102}",
        "timestamp": timestamp_now,
        "station_name": payload.station_id,
        "action_taken": f"Protocol Executed: {payload.action_type}",
        "operator": "DISPATCH_CONSOLE"
    })

    return {
        "status": "SUCCESS",
        "incident_id": payload.incident_id,
        "message": f"Safety protocol '{payload.action_type}' triggered for station {payload.station_id}."
    }