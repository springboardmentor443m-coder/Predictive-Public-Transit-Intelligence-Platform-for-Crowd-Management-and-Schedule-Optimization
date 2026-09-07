from typing import List
from fastapi import APIRouter
from app.services.alert_service import alert_service
from app.schemas.alert_schema import AlertItem, PABroadcastRequest, BroadcastResponse

router = APIRouter()


@router.get("/", response_model=List[AlertItem])
async def get_active_alerts():
    return await alert_service.get_active_alerts()


@router.post("/broadcast", response_model=BroadcastResponse)
async def trigger_pa_broadcast(request: PABroadcastRequest):
    return await alert_service.trigger_pa_broadcast(request)


@router.post("/resolve/{alert_id}")
async def resolve_alert(alert_id: str):
    success = await alert_service.resolve_alert(alert_id)
    return {"alert_id": alert_id, "resolved": success}
