"""
Database Configuration — SQLite with SQLAlchemy + AsyncIO
Stores prediction history for analytics and auditing.
"""
from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession, async_sessionmaker
from sqlalchemy.orm import DeclarativeBase, Mapped, mapped_column
from sqlalchemy import DateTime, Float, Integer, String, Text, Boolean, select, func
from datetime import datetime
import os

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
DATABASE_URL = f"sqlite+aiosqlite:///{os.path.join(BASE_DIR, 'metroflow_predictions.db')}"

engine = create_async_engine(DATABASE_URL, echo=False)
async_session = async_sessionmaker(engine, class_=AsyncSession, expire_on_commit=False)

class Base(DeclarativeBase):
    pass

class PredictionRecord(Base):
    __tablename__ = "predictions"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    from_station: Mapped[str] = mapped_column(String(50), default="Unknown")
    to_station: Mapped[str] = mapped_column(String(50), default="Unknown")
    line_color: Mapped[str] = mapped_column(String(50), default="Unknown")
    entry_hour: Mapped[int] = mapped_column(Integer, default=0)
    day_of_week: Mapped[str] = mapped_column(String(20), default="Monday")
    train_capacity: Mapped[int] = mapped_column(Integer, default=2400)
    predicted_occupancy: Mapped[float] = mapped_column(Float, default=0.0)
    occupancy_rate_pct: Mapped[float] = mapped_column(Float, default=0.0)
    recommended_headway: Mapped[int] = mapped_column(Integer, default=5)
    traffic_tier: Mapped[str] = mapped_column(String(20), default="OFF_PEAK")
    fleet_action: Mapped[str] = mapped_column(Text, default="")
    alert_level: Mapped[str] = mapped_column(String(30), default="NORMAL")
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)

class User(Base):
    __tablename__ = "users"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    username: Mapped[str] = mapped_column(String(50), unique=True, nullable=False, index=True)
    hashed_password: Mapped[str] = mapped_column(String(255), nullable=False)
    role: Mapped[str] = mapped_column(String(20), default="admin")
    is_active: Mapped[bool] = mapped_column(Boolean, default=True)

async def init_db():
    """Create all tables if they don't exist."""
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)

async def save_prediction(record: PredictionRecord):
    """Save a prediction to the database."""
    async with async_session() as session:
        async with session.begin():
            session.add(record)
        await session.commit()

async def get_prediction_history(limit: int = 100):
    """Retrieve recent prediction history."""
    async with async_session() as session:
        result = await session.execute(
            select(PredictionRecord).order_by(PredictionRecord.created_at.desc()).limit(limit)
        )
        return result.scalars().all()

async def get_prediction_stats():
    """Get aggregated prediction statistics."""
    async with async_session() as session:
        result = await session.execute(
            select(
                func.count(PredictionRecord.id).label('total'),
                func.avg(PredictionRecord.predicted_occupancy).label('avg_occ'),
                func.max(PredictionRecord.predicted_occupancy).label('max_occ'),
            ).select_from(PredictionRecord)
        )
        row = result.first()
        return {"total": row.total, "avg_occ": row.avg_occ, "max_occ": row.max_occ} if row else {"total": 0, "avg_occ": 0, "max_occ": 0}

async def get_user_by_username(username: str):
    """Get a user by username."""
    async with async_session() as session:
        result = await session.execute(select(User).where(User.username == username))
        return result.scalar_one_or_none()

async def create_user(username: str, hashed_password: str, role: str = "user"):
    """Create a new user."""
    async with async_session() as session:
        async with session.begin():
            user = User(username=username, hashed_password=hashed_password, role=role, is_active=True)
            session.add(user)
        await session.commit()
        return user
