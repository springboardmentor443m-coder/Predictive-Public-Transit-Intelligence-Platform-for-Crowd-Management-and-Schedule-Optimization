from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session
from sqlalchemy import text
from app.api.deps import get_db
from app.core.config import settings

router = APIRouter()


@router.get("/health", summary="System Health Check")
def health_check(db: Session = Depends(get_db)):
    """Check backend operational health and database connectivity."""
    db_status = "healthy"
    try:
        db.execute(text("SELECT 1"))
    except Exception as e:
        db_status = f"unhealthy: {str(e)}"

    return {
        "status": "online",
        "service": settings.PROJECT_NAME,
        "database": db_status,
        "live_data_provider": settings.LIVE_DATA_PROVIDER_TYPE
    }
