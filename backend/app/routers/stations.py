from typing import List, Optional
from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy.orm import Session
from sqlalchemy import select, or_
from app.database import get_db
from app.models.station import Station
from app.schemas.station import StationResponse

router = APIRouter(prefix="/stations", tags=["Stations"])


@router.get(
    "",
    response_model=List[StationResponse],
    summary="List, search, and filter stations",
    description="Retrieve all stations or filter by partial name search, line name, or district.",
)
def list_stations(
    search: Optional[str] = Query(None, description="Partial search match on station name (English or Korean)"),
    line: Optional[str] = Query(None, description="Filter by exact transit line (e.g. 'Line 2')"),
    district: Optional[str] = Query(None, description="Filter by administrative district (e.g. 'Gangnam-gu')"),
    db: Session = Depends(get_db),
):
    query = select(Station)

    if search:
        search_pattern = f"%{search.strip()}%"
        query = query.where(
            or_(
                Station.name_en.ilike(search_pattern),
                Station.name_kr.ilike(search_pattern),
                Station.station_code.ilike(search_pattern),
            )
        )

    if line:
        query = query.where(Station.line == line.strip())

    if district:
        query = query.where(Station.district == district.strip())

    query = query.order_by(Station.line, Station.name_en)
    stations = db.execute(query).scalars().all()
    return stations


@router.get(
    "/{station_code}",
    response_model=StationResponse,
    summary="Get single station details",
    description="Retrieve full metadata for a single station by its unique station code.",
    responses={
        404: {"description": "Station not found in network"}
    }
)
def get_station_detail(
    station_code: str,
    db: Session = Depends(get_db),
):
    station = db.execute(
        select(Station).where(Station.station_code == station_code.strip())
    ).scalar_one_or_none()

    if not station:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Station with code '{station_code}' not found.",
        )
    return station
