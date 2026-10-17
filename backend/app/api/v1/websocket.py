from datetime import datetime, timezone
from fastapi import APIRouter, WebSocket, WebSocketDisconnect, Query
from pydantic import BaseModel
from app.core.events import manager
from app.core.security import decode_access_token

router = APIRouter()


class TestEventPayload(BaseModel):
    event_type: str = "TEST_SYSTEM_PING"
    message: str = "Development test event verifying WebSocket infrastructure."


@router.websocket("/ws/events")
async def websocket_events_endpoint(
    websocket: WebSocket,
    token: str = Query(default=None, description="JWT bearer token for WebSocket authentication")
):
    """
    Real-time WebSocket endpoint for MetroFlow operation updates.
    
    Requires a valid JWT `token` query parameter (same token issued at login).
    Connected clients receive real-time broadcast events (vehicle positions, alerts, delays).
    """
    # --- Authenticate before accepting connection ---
    if not token:
        await websocket.close(code=4001)
        return

    payload = decode_access_token(token)
    if not payload:
        await websocket.close(code=4001)
        return

    user_id = payload.get("sub")
    if not user_id:
        await websocket.close(code=4001)
        return

    await manager.connect(websocket)
    try:
        # Send initial connection handshake confirmation
        await manager.send_personal_message(
            {
                "event": "CONNECTION_ESTABLISHED",
                "timestamp": datetime.now(timezone.utc).isoformat(),
                "data_state": "LIVE",
                "message": "Connected to MetroFlow Real-Time Event Infrastructure",
                "user_id": str(user_id)
            },
            websocket
        )
        while True:
            # Maintain active connection, listening for client pings/messages
            data = await websocket.receive_text()
            await manager.send_personal_message(
                {
                    "event": "ACK",
                    "echo": data,
                    "timestamp": datetime.now(timezone.utc).isoformat()
                },
                websocket
            )
    except WebSocketDisconnect:
        manager.disconnect(websocket)


@router.post("/ws/test-event", summary="Trigger Test Broadcast Event [DEV INFRASTRUCTURE ONLY]")
async def trigger_test_event(payload: TestEventPayload):
    """
    Development-only endpoint to broadcast a test ping across connected WebSockets.
    
    Explicitly labeled as DEV_INFRASTRUCTURE_TEST (never operational transportation data).
    """
    event_data = {
        "event": payload.event_type,
        "data_state": "DEV_INFRASTRUCTURE_TEST",
        "timestamp": datetime.now(timezone.utc).isoformat(),
        "payload": {
            "message": payload.message,
            "note": "Development Test Event - Not Operational Telemetry"
        }
    }
    await manager.broadcast(event_data)
    return {
        "status": "broadcast_sent",
        "active_clients": len(manager.active_connections),
        "event": event_data
    }
