"""
alert_manager.py - Milestone 3
Handles rule-based alert triggering, emergency announcements,
and real-time transit status broadcasts.
"""

from datetime import datetime
from typing import List, Dict, Optional
import pandas as pd
import os

ALERTS_LOG_PATH = os.path.join(os.path.dirname(__file__), "data", "alerts_history.csv")

class AlertManager:
    def __init__(self):
        self.active_alerts: List[Dict] = []
        self.emergency_announcements: List[Dict] = []
        self._init_alert_store()

    def _init_alert_store(self):
        """Ensure historical alerts storage exists."""
        if not os.path.exists(ALERTS_LOG_PATH):
            df = pd.DataFrame(columns=["timestamp", "alert_type", "severity", "target", "message"])
            df.to_csv(ALERTS_LOG_PATH, index=False)

    def evaluate_crowd_thresholds(self, station_name: str, net_flow: int, status: str) -> Optional[Dict]:
        """
        Triggers tiered alerts based on net flow and congestion level.
        """
        alert = None
        now_str = datetime.now().strftime("%Y-%m-%d %H:%M:%S")

        if status == "CRITICAL" or net_flow >= 1200:
            alert = {
                "id": f"ALT-{int(datetime.now().timestamp())}",
                "timestamp": now_str,
                "alert_type": "SURGE_OVERLOAD",
                "severity": "CRITICAL",
                "target": station_name,
                "message": f"Critical commuter surge detected at {station_name} ({net_flow} net accumulation). Implement platform metering.",
                "action_required": "Deploy auxiliary trains; restrict turnstiles."
            }
        elif status == "HIGH" or net_flow >= 800:
            alert = {
                "id": f"ALT-{int(datetime.now().timestamp())}",
                "timestamp": now_str,
                "alert_type": "HIGH_DENSITY",
                "severity": "WARNING",
                "target": station_name,
                "message": f"High density warning at {station_name} ({net_flow} net accumulation).",
                "action_required": "Compress headway to 3-4 minutes."
            }

        if alert:
            self._record_alert(alert)
        return alert

    def evaluate_delay_thresholds(self, route_id: str, delay_minutes: float) -> Optional[Dict]:
        """Triggers alerts if line delays exceed acceptable buffers."""
        if delay_minutes >= 6.0:
            alert = {
                "id": f"ALT-DLY-{int(datetime.now().timestamp())}",
                "timestamp": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
                "alert_type": "SCHEDULE_DISRUPTION",
                "severity": "HIGH" if delay_minutes > 10 else "MODERATE",
                "target": f"Route {route_id}",
                "message": f"Route {route_id} delay has reached {delay_minutes:.1f} mins.",
                "action_required": "Initiate automated schedule rebalancing."
            }
            self._record_alert(alert)
            return alert
        return None

    def broadcast_emergency(self, line: str, severity: str, message: str, operator_id: str) -> Dict:
        """Publishes an operational emergency announcement across stations."""
        announcement = {
            "id": f"EMG-{int(datetime.now().timestamp())}",
            "timestamp": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
            "line": line,
            "severity": severity.upper(),
            "message": message,
            "issued_by": operator_id,
            "status": "ACTIVE"
        }
        self.emergency_announcements.insert(0, announcement)
        self._record_alert({
            "timestamp": announcement["timestamp"],
            "alert_type": "EMERGENCY_BROADCAST",
            "severity": announcement["severity"],
            "target": line,
            "message": message
        })
        return announcement

    def _record_alert(self, alert_entry: Dict):
        """Logs alerts into memory and disk."""
        self.active_alerts.insert(0, alert_entry)
        df_new = pd.DataFrame([{
            "timestamp": alert_entry["timestamp"],
            "alert_type": alert_entry["alert_type"],
            "severity": alert_entry["severity"],
            "target": alert_entry["target"],
            "message": alert_entry["message"]
        }])
        df_new.to_csv(ALERTS_LOG_PATH, mode="a", header=not os.path.exists(ALERTS_LOG_PATH), index=False)

    def get_recent_alerts(self, limit: int = 15) -> List[Dict]:
        return self.active_alerts[:limit]

    def get_active_announcements(self) -> List[Dict]:
        return self.emergency_announcements[:5]

alert_hub = AlertManager()