from sqlalchemy import Column, Integer, String
from app.db.database import Base


class User(Base):
    __tablename__ = "users"
    id = Column(Integer, primary_key=True, index=True)
    username = Column(String(64), unique=True, index=True, nullable=False)
    full_name = Column(String(128), default="")
    hashed_password = Column(String(256), nullable=False)
    role = Column(String(32), default="operator")  # admin | operator | viewer
