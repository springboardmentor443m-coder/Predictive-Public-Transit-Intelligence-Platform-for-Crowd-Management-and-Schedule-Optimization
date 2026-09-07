import uuid
from datetime import datetime, timezone
from typing import List
from app.schemas.alert_schema import AlertItem, PABroadcastRequest, BroadcastResponse
from app.services.crowd_service import live_station_state

# Memory store for active alerts
ACTIVE_ALERTS: List[AlertItem] = []


def initialize_sample_alerts():
    now = datetime.now(timezone.utc)
    ACTIVE_ALERTS.extend([
        AlertItem(
            id=str(uuid.uuid4())[:8],
            station_id=1,
            station_name="Central Terminal",
            line_name="Red Line",
            priority="CRITICAL",
            category="OVERCROWDING",
            message="Platform 2 capacity reached 88.5%. Deploying crowd management personnel.",
            timestamp=now,
            is_resolved=False,
        ),
        AlertItem(
            id=str(uuid.uuid4())[:8],
            station_id=11,
            station_name="Central Terminal (Blue)",
            line_name="Blue Line",
            priority="WARNING",
            category="TRAIN_DELAY",
            message="Train BLU-TR-01 delayed by +8 minutes due to signal alignment check.",
            timestamp=now,
            is_resolved=False,
        ),
        AlertItem(
            id=str(uuid.uuid4())[:8],
            station_id=15,
            station_name="Stadium Arena",
            line_name="Blue Line",
            priority="INFO",
            category="ANOMALY",
            message="Scheduled concert event footfall surge anticipated between 18:30 and 21:00.",
            timestamp=now,
            is_resolved=False,
        ),
    ])


initialize_sample_alerts()


class AlertService:
    @staticmethod
    async def get_active_alerts() -> List[AlertItem]:
        now = datetime.now(timezone.utc)
        
        # Dynamically check current live station densities for new threshold breaches
        for st_data in live_station_state.values():
            if st_data["density_percentage"] >= 80.0:
                # Check if alert already exists
                existing = any(
                    a.station_id == st_data["station_id"] and a.category == "OVERCROWDING" and not a.is_resolved
                    for a in ACTIVE_ALERTS
                )
                if not existing:
                    ACTIVE_ALERTS.insert(0, AlertItem(
                        id=str(uuid.uuid4())[:8],
                        station_id=st_data["station_id"],
                        station_name=st_data["station_name"],
                        line_name=st_data["line_name"],
                        priority="CRITICAL",
                        category="OVERCROWDING",
                        message=f"Density alert! {st_data['station_name']} platform load at {st_data['density_percentage']}%.",
                        timestamp=now,
                        is_resolved=False,
                    ))

        return ACTIVE_ALERTS

    @staticmethod
    async def trigger_pa_broadcast(request: PABroadcastRequest) -> BroadcastResponse:
        broadcast_id = f"PA-BC-{str(uuid.uuid4())[:6].upper()}"
        now = datetime.now(timezone.utc)
        
        # Log stub message for SMTP / SMS / Public Address systems
        print(f"[PA BROADCAST] ID: {broadcast_id} | Priority: {request.priority}")
        print(f"Target Stations: {request.station_ids} | Message: {request.message}")
        print(f"Channels Notified: PA System, SMS Gateway, Operator Console")

        return BroadcastResponse(
            broadcast_id=broadcast_id,
            status="BROADCAST_SENT",
            target_stations_count=len(request.station_ids),
            channels=["PA_SYSTEM", "SMS_GATEWAY", "EMAIL_OPERATORS"],
            timestamp=now
        )

    @staticmethod
    async def resolve_alert(alert_id: str) -> bool:
        for alert in ACTIVE_ALERTS:
            if alert.id == alert_id:
                alert.is_resolved = True
                return True
        return False


alert_service = AlertService()
