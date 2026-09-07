from sqlalchemy import Column, Integer, String

from app.core.database import Base


class Train(Base):
    __tablename__ = "trains"

    id = Column(String, primary_key=True, index=True)
    code = Column(String, unique=True, index=True, nullable=False)
    model = Column(String, nullable=False)
    capacity = Column(Integer, nullable=False, default=1200)
    status = Column(String, default="active", nullable=False)
