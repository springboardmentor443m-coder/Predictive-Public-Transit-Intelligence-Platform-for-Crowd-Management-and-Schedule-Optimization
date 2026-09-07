from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from app.core.deps import get_db, require_roles
from app.models.station import Station
from app.schemas.station import StationRead

router = APIRouter(prefix="/stations", tags=["stations"])


@router.get("", response_model=list[StationRead])
async def list_stations(db: Session = Depends(get_db), _=Depends(require_roles())):
    return db.query(Station).all()


@router.get("/{station_id}", response_model=StationRead)
async def get_station(station_id: str, db: Session = Depends(get_db), _=Depends(require_roles())):
    station = db.query(Station).filter(Station.id == station_id).first()
    if not station:
        raise HTTPException(status_code=404, detail="Station not found")
    return station
