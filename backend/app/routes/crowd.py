from fastapi import APIRouter, Depends
from sqlalchemy import text
from sqlalchemy.orm import Session
from app.routes.auth import get_current_user
from app.core.database import get_db


router = APIRouter(
    prefix="/api/crowd",
    tags=["Crowd Monitoring"]
)


@router.get("/summary")
def crowd_summary(
    db: Session = Depends(get_db),
    current_user = Depends(get_current_user)
):
    total_records = db.execute(
        text("SELECT COUNT(*) FROM crowd_evacuation")
    ).scalar()

    route_status = db.execute(
        text("""
            SELECT route_status, COUNT(*) AS count
            FROM crowd_evacuation
            GROUP BY route_status
            ORDER BY count DESC
        """)
    ).mappings().all()

    scenarios = db.execute(
        text("""
            SELECT scenario, COUNT(*) AS count
            FROM crowd_evacuation
            GROUP BY scenario
            ORDER BY count DESC
        """)
    ).mappings().all()

    return {
        "total_records": total_records,
        "route_status": [
            {
                "status": row["route_status"],
                "count": row["count"]
            }
            for row in route_status
        ],
        "scenarios": [
            {
                "scenario": row["scenario"],
                "count": row["count"]
            }
            for row in scenarios
        ]
    }