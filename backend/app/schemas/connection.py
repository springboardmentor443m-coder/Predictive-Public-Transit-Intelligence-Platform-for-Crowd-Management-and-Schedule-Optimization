from pydantic import BaseModel


class StationConnection(BaseModel):
    from_code: str
    to_code: str
    kind: str
    vias: str