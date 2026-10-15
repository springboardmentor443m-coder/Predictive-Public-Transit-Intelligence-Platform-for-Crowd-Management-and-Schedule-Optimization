from fastapi import APIRouter, Response
from pydantic import BaseModel
import csv
import io

router = APIRouter(prefix="/api/reports", tags=["Reports & Settings"])

# Default system threshold settings
SYSTEM_SETTINGS = {
    "normal_threshold_pct": 60,
    "elevated_threshold_pct": 80,
    "auto_dispatch_enabled": True,
    "telemetry_interval_sec": 10
}

class ThresholdUpdate(BaseModel):
    normal_threshold_pct: int
    elevated_threshold_pct: int
    auto_dispatch_enabled: bool

@router.get("/summary")
def get_historical_summary():
    return {
        "weekly_footfall": 1284500,
        "on_time_dispatch_rate_pct": 98.4,
        "bottlenecks_mitigated": 38,
        "peak_hour": "08:30 - 09:30 & 18:00 - 19:30",
        "corridor_breakdown": [
            {"name": "Blue Corridor", "volume": 580000, "avg_load_pct": 74},
            {"name": "Emerald Express", "volume": 420000, "avg_load_pct": 52},
            {"name": "Ruby Loop", "volume": 284500, "avg_load_pct": 66}
        ],
        "settings": SYSTEM_SETTINGS
    }

@router.post("/settings")
def update_settings(payload: ThresholdUpdate):
    SYSTEM_SETTINGS["normal_threshold_pct"] = payload.normal_threshold_pct
    SYSTEM_SETTINGS["elevated_threshold_pct"] = payload.elevated_threshold_pct
    SYSTEM_SETTINGS["auto_dispatch_enabled"] = payload.auto_dispatch_enabled
    return {
        "status": "SUCCESS",
        "message": "System operational thresholds updated.",
        "settings": SYSTEM_SETTINGS
    }

@router.get("/export/csv")
def export_csv_report():
    output = io.StringIO()
    writer = csv.writer(output)
    
    # Headers
    writer.writerow(["Station ID", "Station Name", "Corridor", "Peak Inflow/min", "Peak Density %", "Status"])
    
    # Telemetry rows
    records = [
        ["ST-01", "Central Terminal", "Blue Corridor", "280", "76%", "ELEVATED"],
        ["ST-02", "Tech Hub Junction", "Interchange", "380", "89%", "CRITICAL"],
        ["ST-03", "Cyber Gateway", "Interchange", "160", "58%", "NORMAL"],
        ["ST-04", "Financial District", "Blue Corridor", "310", "83%", "CRITICAL"],
        ["ST-05", "South Port", "Emerald Express", "95", "41%", "NORMAL"],
        ["ST-06", "Market Square", "Emerald Express", "135", "52%", "NORMAL"]
    ]
    
    for row in records:
        writer.writerow(row)
        
    output.seek(0)
    return Response(
        content=output.getvalue(),
        media_type="text/csv",
        headers={"Content-Disposition": "attachment; filename=metroflow_operations_report.csv"}
    )