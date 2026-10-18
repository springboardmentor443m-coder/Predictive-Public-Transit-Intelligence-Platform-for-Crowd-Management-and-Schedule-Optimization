"""
MetroFlow Alert & Emergency Notification Module
Handles real-time overcrowding alerts, emergency passenger broadcasts,
line delay advisories, and operator acknowledgment workflows.
"""

from fastapi import APIRouter, HTTPException, Depends
from pydantic import BaseModel
from typing import Optional, List
from db.database import get_db_connection
from routes.auth import get_current_user

router = APIRouter(prefix="/api/alerts", tags=["Alerts & Notifications"])

class BroadcastRequest(BaseModel):
    severity: str # 'info', 'warning', 'critical', 'emergency'
    category: str # 'emergency', 'overcrowding', 'delay', 'maintenance'
    station_id: Optional[str] = "NYC-NETWORK"
    station_name: Optional[str] = "Network-Wide Announcement"
    line: Optional[str] = "ALL"
    message: str

@router.get("")
def list_active_alerts():
    """Returns active and recent operational alerts and warnings."""
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute("""
    SELECT id, severity, category, station_id, station_name, line, message, timestamp, is_active, resolved_by
    FROM alerts
    ORDER BY is_active DESC, id DESC
    LIMIT 30
    """)
    alerts = [dict(r) for r in cursor.fetchall()]
    conn.close()
    return {"alerts": alerts, "active_count": sum(1 for a in alerts if a["is_active"])}

@router.post("/broadcast")
def broadcast_announcement(req: BroadcastRequest, current_user: dict = Depends(get_current_user)):
    """Broadcasts a high-priority operational emergency alert across station digital displays."""
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute("""
    INSERT INTO alerts (severity, category, station_id, station_name, line, message, is_active)
    VALUES (?, ?, ?, ?, ?, ?, 1)
    """, (req.severity, req.category, req.station_id, req.station_name, req.line, req.message))

    # Audit log
    details = f"Broadcasted {req.severity.upper()} notice: {req.message[:80]}"
    cursor.execute("""
    INSERT INTO operational_logs (user_name, role, action, details)
    VALUES (?, ?, 'BROADCAST_ALERT', ?)
    """, (current_user.get("name", "Dispatcher"), current_user.get("role", "operator"), details))

    conn.commit()
    conn.close()

    return {"success": True, "message": "Emergency alert broadcasted successfully"}

@router.post("/{alert_id}/resolve")
def resolve_alert(alert_id: int, current_user: dict = Depends(get_current_user)):
    """Acknowledges and marks an alert as resolved."""
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute("""
    UPDATE alerts
    SET is_active = 0, resolved_by = ?
    WHERE id = ?
    """, (current_user.get("name", "Operator"), alert_id))

    cursor.execute("""
    INSERT INTO operational_logs (user_name, role, action, details)
    VALUES (?, ?, 'ALERT_RESOLVED', ?)
    """, (current_user.get("name", "Operator"), current_user.get("role", "operator"), f"Resolved alert #{alert_id}"))

    conn.commit()
    conn.close()

    return {"success": True, "alert_id": alert_id, "resolved_by": current_user.get("name")}
