"""
MetroFlow Train Scheduling & Headway Optimization Module
Supports dynamic headway adjustment, peak-hour frequency optimization,
and real-time train delay handling.
"""

from fastapi import APIRouter, HTTPException, Depends
from pydantic import BaseModel
from typing import List, Optional
from db.database import get_db_connection
from routes.auth import get_current_user
from simulator.live_engine import simulator

router = APIRouter(prefix="/api/scheduling", tags=["Scheduling Management"])

class HeadwayAdjustRequest(BaseModel):
    line: str
    target_headway: float # in minutes
    reason: Optional[str] = "Passenger demand surge mitigation"

class DelayReportRequest(BaseModel):
    train_id: str
    delay_minutes: int
    cause: str # 'signal_malfunction', 'passenger_medical', 'track_obstruction', 'door_hold'

@router.get("/lines")
def get_all_line_schedules():
    """Returns real-time schedules, headways, and operational status for all lines."""
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute("SELECT * FROM line_schedules ORDER BY line ASC")
    lines = [dict(r) for r in cursor.fetchall()]
    conn.close()
    return {"lines": lines}

@router.post("/frequency-adjust")
def adjust_line_frequency(req: HeadwayAdjustRequest, current_user: dict = Depends(get_current_user)):
    """Adjusts train headway (frequency) on a specific subway line."""
    if req.target_headway < 2.0 or req.target_headway > 15.0:
        raise HTTPException(status_code=400, detail="Headway must be between 2.0 and 15.0 minutes")

    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute("SELECT * FROM line_schedules WHERE line = ?", (req.line,))
    line_row = cursor.fetchone()
    if not line_row:
        conn.close()
        raise HTTPException(status_code=404, detail="Subway line not found")

    old_headway = line_row["current_headway"]
    cursor.execute("""
    UPDATE line_schedules 
    SET current_headway = ?, last_updated = CURRENT_TIMESTAMP
    WHERE line = ?
    """, (req.target_headway, req.line))

    # Audit log
    details = f"Adjusted Line {req.line} headway from {old_headway}m to {req.target_headway}m. Reason: {req.reason}"
    cursor.execute("""
    INSERT INTO operational_logs (user_name, role, action, details)
    VALUES (?, ?, 'HEADWAY_ADJUSTMENT', ?)
    """, (current_user.get("name", "Operator"), current_user.get("role", "operator"), details))

    conn.commit()
    conn.close()

    return {
        "success": True,
        "line": req.line,
        "previous_headway": old_headway,
        "new_headway": req.target_headway,
        "action_recorded": details
    }

@router.post("/optimize-peak")
def optimize_all_peak_schedules(current_user: dict = Depends(get_current_user)):
    """
    Executes automated optimization workflow: analyzes current network crowd pressure
    and automatically tightens headway on overloaded lines (e.g. Lines 1, 4, 7, A).
    """
    conn = get_db_connection()
    cursor = conn.cursor()
    
    # Check severe stations to identify overloaded lines
    overloaded_lines = set()
    for s in simulator.stations_data.values():
        if s["density_percent"] >= 70:
            for l in s["lines"]:
                overloaded_lines.add(l)

    optimized_count = 0
    for line in overloaded_lines:
        cursor.execute("UPDATE line_schedules SET current_headway = MAX(2.5, current_headway * 0.75), peak_status = 'Peak' WHERE line = ?", (line,))
        optimized_count += 1

    details = f"Triggered Automated Peak Schedule Optimization across {optimized_count} active corridor lines."
    cursor.execute("""
    INSERT INTO operational_logs (user_name, role, action, details)
    VALUES (?, ?, 'PEAK_OPTIMIZATION', ?)
    """, (current_user.get("name", "Director"), current_user.get("role", "admin"), details))

    conn.commit()
    conn.close()

    return {
        "success": True,
        "optimized_lines_count": optimized_count,
        "optimized_lines": list(overloaded_lines),
        "message": "Peak frequency adjustments applied across active transit network"
    }

@router.post("/report-delay")
def report_train_delay(req: DelayReportRequest, current_user: dict = Depends(get_current_user)):
    """Simulates or records an operational train delay and alerts connected stations."""
    # Find train in simulator
    target_train = None
    for tr in simulator.trains_data:
        if tr["id"] == req.train_id:
            target_train = tr
            break

    if not target_train:
        # Default to first train if ID not found
        target_train = simulator.trains_data[0]

    target_train["delay_seconds"] = req.delay_minutes * 60
    target_train["status"] = "Delayed"

    conn = get_db_connection()
    cursor = conn.cursor()
    # Insert system alert
    cursor.execute("""
    INSERT INTO alerts (severity, category, station_id, station_name, line, message, is_active)
    VALUES ('warning', 'delay', ?, ?, ?, ?, 1)
    """, (
        target_train["from_station_id"],
        target_train["from_station_name"],
        target_train["line"],
        f"Train {target_train['id']} on Line {target_train['line']} delayed by {req.delay_minutes} min due to {req.cause.replace('_', ' ')}."
    ))

    # Audit log
    details = f"Reported {req.delay_minutes}m delay on Train {target_train['id']} ({req.cause})"
    cursor.execute("""
    INSERT INTO operational_logs (user_name, role, action, details)
    VALUES (?, ?, 'DELAY_REPORTED', ?)
    """, (current_user.get("name", "Dispatcher"), current_user.get("role", "operator"), details))

    conn.commit()
    conn.close()

    return {
        "success": True,
        "train_id": target_train["id"],
        "line": target_train["line"],
        "delay_recorded_minutes": req.delay_minutes
    }
