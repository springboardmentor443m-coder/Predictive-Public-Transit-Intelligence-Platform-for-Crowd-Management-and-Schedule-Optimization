from fastapi import APIRouter
from datetime import datetime

router = APIRouter(prefix="/api/dashboard", tags=["Dashboard"])

@router.get("/summary")
def get_dashboard_summary():
    return {
        "network_status": "OPTIMAL",
        "system_time": datetime.utcnow().isoformat(),
        "metrics": {
            "total_passengers_today": 142850,
            "active_stations": 24,
            "total_stations": 24,
            "average_congestion_pct": 58.4,
            "active_alerts_count": 2
        },
        "station_quick_status": [
            {"id": "ST-01", "name": "Central Terminal", "line": "Blue", "congestion": 74, "status": "ELEVATED"},
            {"id": "ST-02", "name": "Tech Hub Junction", "line": "Cyan", "congestion": 82, "status": "CRITICAL"},
            {"id": "ST-03", "name": "Market Square", "line": "Green", "congestion": 45, "status": "NORMAL"},
            {"id": "ST-04", "name": "Airport Link", "line": "Blue", "congestion": 38, "status": "NORMAL"}
        ],
        "critical_alerts": [
            {
                "id": "ALT-101",
                "station": "Tech Hub Junction",
                "type": "Overcrowding Surge (>80%)",
                "severity": "CRITICAL",
                "time": "3 mins ago"
            },
            {
                "id": "ALT-102",
                "station": "Central Terminal",
                "type": "Platform Door Delay Notice",
                "severity": "WARNING",
                "time": "7 mins ago"
            }
        ]
    }