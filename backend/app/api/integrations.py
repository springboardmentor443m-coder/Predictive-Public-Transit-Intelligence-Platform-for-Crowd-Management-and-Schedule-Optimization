from fastapi import APIRouter, HTTPException
from pydantic import BaseModel
from typing import Optional, List
from datetime import datetime

router = APIRouter(prefix="/api/integrations", tags=["External Integrations & Transit APIs"])

class AlertPayload(BaseModel):
    station_id: Optional[str] = "ALL_STATIONS"
    channels: List[str] = ["EMAIL", "SMS", "PUSH_NOTIFICATION", "PUBLIC_ADDRESS"]
    priority: str = "HIGH"
    message: str

# 1. Third-party Transit Open Feed (e.g. for Google Maps, City Transport Apps)
@router.get("/third-party/transit-feed")
async def get_third_party_transit_feed():
    """
    Open Transit Data API consumed by third-party navigation providers (Google Maps, Apple Maps, City Transit)
    Provides live headway, station congestion index, and platform crowd advisories.
    """
    return {
        "agency": {
            "name": "Seoul Metro - MetroFlow Intelligence",
            "timezone": "Asia/Seoul",
            "api_spec": "GTFS-RT / REST JSON v1.0",
            "last_updated": datetime.utcnow().isoformat() + "Z"
        },
        "routes": [
            {
                "line_id": "LINE-01",
                "name": "Blue Corridor",
                "current_headway_min": 3.5,
                "status": "OPERATIONAL",
                "congestion_level": "ELEVATED_SURGE",
                "recommended_alternative": "Emerald Express"
            },
            {
                "line_id": "LINE-02",
                "name": "Emerald Express",
                "current_headway_min": 5.0,
                "status": "OPERATIONAL",
                "congestion_level": "NOMINAL",
                "recommended_alternative": None
            },
            {
                "line_id": "LINE-03",
                "name": "Ruby Loop",
                "current_headway_min": 7.0,
                "status": "OPERATIONAL",
                "congestion_level": "NOMINAL",
                "recommended_alternative": None
            }
        ]
    }

# 2. Centralized External Alert Dispatcher (Email, SMS, Push, PA)
@router.post("/dispatch-alert")
async def dispatch_external_alert(payload: AlertPayload):
    """
    Triggers simulated external services:
    - SMTP / SendGrid (Email Service)
    - Twilio / Telephony Gateway (SMS Service)
    - Firebase Cloud Messaging / APNS (Mobile Push)
    - Station Edge Controllers (Public Address System)
    """
    timestamp = datetime.utcnow().isoformat() + "Z"
    dispatched_channels = {}

    for channel in payload.channels:
        channel_upper = channel.upper()
        if channel_upper == "EMAIL":
            dispatched_channels["EMAIL"] = {
                "status": "QUEUED_AND_SENT",
                "gateway": "SMTP / SendGrid Transit Relay",
                "recipients": "operations-control@metroflow.live",
                "timestamp": timestamp
            }
        elif channel_upper == "SMS":
            dispatched_channels["SMS"] = {
                "status": "DISPATCHED",
                "gateway": "Twilio SMS Gateway",
                "target_group": "Active Station Masters (Nodes ST-01 to ST-12)",
                "timestamp": timestamp
            }
        elif channel_upper == "PUSH_NOTIFICATION":
            dispatched_channels["PUSH_NOTIFICATION"] = {
                "status": "BROADCAST_COMPLETED",
                "service": "Firebase Cloud Messaging (FCM)",
                "audience": "Seoul Metro Passenger Mobile App Users",
                "timestamp": timestamp
            }
        elif channel_upper == "PUBLIC_ADDRESS":
            dispatched_channels["PUBLIC_ADDRESS"] = {
                "status": "AUDIO_SYNTHESIS_BROADCASTING",
                "node": payload.station_id,
                "speakers_online": 96,
                "timestamp": timestamp
            }

    return {
        "success": True,
        "message_broadcast": payload.message,
        "priority": payload.priority,
        "channels_dispatched": dispatched_channels
    }