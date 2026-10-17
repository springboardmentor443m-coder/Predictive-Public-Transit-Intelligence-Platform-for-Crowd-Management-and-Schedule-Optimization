from datetime import datetime
from typing import Optional, Any, Dict
from pydantic import BaseModel, ConfigDict


class AuditLogCreate(BaseModel):
    actor_id: Optional[int] = None
    actor_email: Optional[str] = None
    action: str
    ip_address: Optional[str] = None
    metadata_json: Optional[Dict[str, Any]] = None


class AuditLogResponse(BaseModel):
    id: int
    actor_id: Optional[int] = None
    actor_email: Optional[str] = None
    action: str
    ip_address: Optional[str] = None
    metadata_json: Optional[Dict[str, Any]] = None
    created_at: datetime

    model_config = ConfigDict(from_attributes=True)
