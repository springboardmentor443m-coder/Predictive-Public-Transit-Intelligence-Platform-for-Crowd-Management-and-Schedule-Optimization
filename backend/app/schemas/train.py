from typing import Optional

from pydantic import BaseModel, ConfigDict


class TrainBase(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    code: str
    model: str
    capacity: int = 1200
    status: str = "active"


class TrainCreate(TrainBase):
    id: str


class TrainRead(TrainBase):
    id: str
