from typing import List, Optional
from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session
from app.api.deps import get_db, require_admin
from app.models.user import User
from app.schemas.audit import AuditLogResponse
from app.services.audit_service import AuditService

router = APIRouter(dependencies=[Depends(require_admin)])


@router.get("/audit-logs", response_model=List[AuditLogResponse], summary="Retrieve System Audit Logs (Admin Only)")
def get_audit_logs(
    skip: int = 0,
    limit: int = 50,
    action: Optional[str] = None,
    actor_email: Optional[str] = None,
    db: Session = Depends(get_db)
):
    """Retrieve audit logs with optional filtering by action or actor email."""
    logs = AuditService.get_logs(
        db,
        skip=skip,
        limit=limit,
        action_filter=action,
        actor_email_filter=actor_email
    )
    return [AuditLogResponse.model_validate(l) for l in logs]
