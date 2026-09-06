from sqlalchemy import Column, BigInteger, String, DateTime
from app.core.database import Base


class MetroTransaction(Base):
    __tablename__ = "metro_transactions"

    id = Column(BigInteger, primary_key=True, index=True)

    time = Column(DateTime)
    line_id = Column(String)
    station_id = Column(String)
    device_id = Column(String)
    status = Column(String)
    user_id = Column(String)
    pay_type = Column(String)