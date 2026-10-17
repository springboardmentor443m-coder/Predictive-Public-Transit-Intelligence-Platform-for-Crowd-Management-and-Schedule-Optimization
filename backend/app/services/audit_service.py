import logging
from typing import Optional, Dict, Any
from sqlalchemy.orm import Session
from app.models.audit import AuditLog
from app.schemas.audit import AuditLogCreate

logger = logging.getLogger("metroflow.audit")


class AuditService:
    """Service for recording security, administrative, and system audit log events."""

    @staticmethod
    def create_log(
        db: Session,
        action: str,
        actor_id: Optional[int] = None,
        actor_email: Optional[str] = None,
        ip_address: Optional[str] = None,
        metadata: Optional[Dict[str, Any]] = None
    ) -> AuditLog:
        """Create and persist a new AuditLog entry."""
        audit_entry = AuditLog(
            actor_id=actor_id,
            actor_email=actor_email,
            action=action,
            ip_address=ip_address,
            metadata_json=metadata or {}
        )
        db.add(audit_entry)
        db.commit()
        db.refresh(audit_entry)
        
        logger.info(f"AUDIT_LOG: [{action}] actor={actor_email or actor_id or 'anonymous'}")
        return audit_entry

    @staticmethod
    def get_logs(
        db: Session,
        skip: int = 0,
        limit: int = 50,
        action_filter: Optional[str] = None,
        actor_email_filter: Optional[str] = None
    ):
        query = db.query(AuditLog)
        if action_filter:
            query = query.filter(AuditLog.action == action_filter)
        if actor_email_filter:
            query = query.filter(AuditLog.actor_email.ilike(f"%{actor_email_filter}%"))
        
        return query.order_by(AuditLog.created_at.desc()).offset(skip).limit(limit).all()

    @staticmethod
    def count_logs(
        db: Session,
        action_filter: Optional[str] = None,
        actor_email_filter: Optional[str] = None
    ) -> int:
        query = db.query(AuditLog)
        if action_filter:
            query = query.filter(AuditLog.action == action_filter)
        if actor_email_filter:
            query = query.filter(AuditLog.actor_email.ilike(f"%{actor_email_filter}%"))
        return query.count()
