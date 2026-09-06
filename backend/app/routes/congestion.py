from fastapi import APIRouter, Depends
from sqlalchemy import text
from sqlalchemy.orm import Session
from app.core.security import require_operator_or_admin
from app.core.database import get_db


router = APIRouter(
    prefix="/api/congestion",
    tags=["Congestion Tracking"]
)


@router.get("/summary")
def congestion_summary(
    db: Session = Depends(get_db),
    current_user = Depends(require_operator_or_admin)
):
    # Overall traffic statistics
    overall = db.execute(
        text("""
            SELECT
                COUNT(*) AS total_records,
                COALESCE(SUM(entries), 0) AS total_entries,
                COALESCE(SUM(exits), 0) AS total_exits
            FROM nyc_subway_traffic
        """)
    ).mappings().one()

    # Stations with the highest combined entry and exit activity
    top_stations = db.execute(
        text("""
            SELECT
                stop_name,
                COALESCE(SUM(entries), 0) AS entries,
                COALESCE(SUM(exits), 0) AS exits,
                COALESCE(SUM(entries), 0)
                    + COALESCE(SUM(exits), 0) AS total_activity
            FROM nyc_subway_traffic
            GROUP BY stop_name
            ORDER BY total_activity DESC
            LIMIT 10
        """)
    ).mappings().all()

    return {
        "total_records": overall["total_records"],
        "total_entries": overall["total_entries"],
        "total_exits": overall["total_exits"],
        "top_congested_stations": [
            {
                "station": row["stop_name"],
                "entries": row["entries"],
                "exits": row["exits"],
                "total_activity": row["total_activity"]
            }
            for row in top_stations
        ]
    }