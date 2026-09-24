import os
from datetime import datetime, timedelta
from typing import Optional

from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession, async_sessionmaker
from sqlalchemy.orm import DeclarativeBase, Mapped, mapped_column
from sqlalchemy import select, func, DateTime, String, Integer, Float, Boolean, Text

# --- Database Configuration ---
# Default to SQLite for local development
# To use PostgreSQL, set DATABASE_URL environment variable:
# export DATABASE_URL="postgresql+asyncpg://user:pass@host:5432/metroflow"
DATABASE_URL = os.getenv(
    "DATABASE_URL",
    "sqlite+aiosqlite:///./metroflow_predictions.db"
)

engine = create_async_engine(DATABASE_URL, echo=False)
async_session = async_sessionmaker(engine, class_=AsyncSession, expire_on_commit=False)

class Base(DeclarativeBase):
    pass

class PredictionRecord(Base):
    __tablename__ = "predictions"
    
    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    from_station: Mapped[str] = mapped_column(String(100), nullable=False)
    to_station: Mapped[str] = mapped_column(String(100), nullable=False)
    line_color: Mapped[str] = mapped_column(String(50), nullable=False)
    entry_hour: Mapped[int] = mapped_column(Integer, nullable=False)
    day_of_week: Mapped[str] = mapped_column(String(20), nullable=False)
    train_capacity: Mapped[int] = mapped_column(Integer, nullable=False)
    predicted_occupancy: Mapped[float] = mapped_column(Float, nullable=False)
    occupancy_rate_pct: Mapped[float] = mapped_column(Float, nullable=False)
    recommended_headway_min: Mapped[int] = mapped_column(Integer, nullable=False)
    traffic_tier: Mapped[str] = mapped_column(String(20), nullable=False)
    fleet_action: Mapped[str] = mapped_column(Text, nullable=False)
    alert_level: Mapped[str] = mapped_column(String(50), nullable=False)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)

class User(Base):
    __tablename__ = "users"
    
    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    username: Mapped[str] = mapped_column(String(80), unique=True, nullable=False)
    password_hash: Mapped[str] = mapped_column(String(255), nullable=False)
    role: Mapped[str] = mapped_column(String(20), default="user")
    is_active: Mapped[bool] = mapped_column(Boolean, default=True)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)

# --- Database Functions ---
async def init_db():
    """Create all tables."""
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)

async def get_session() -> AsyncSession:
    async with async_session() as session:
        yield session

async def save_prediction(record: PredictionRecord):
    async with async_session() as session:
        async with session.begin():
            session.add(record)
            await session.commit()

async def get_prediction_history(limit: int = 100):
    async with async_session() as session:
        result = await session.execute(
            select(PredictionRecord).order_by(PredictionRecord.created_at.desc()).limit(limit)
        )
        return result.scalars().all()

async def get_prediction_stats():
    async with async_session() as session:
        result = await session.execute(
            select(
                func.count(PredictionRecord.id),
                func.avg(PredictionRecord.predicted_occupancy),
                func.max(PredictionRecord.predicted_occupancy),
                func.min(PredictionRecord.predicted_occupancy)
            ).select_from(PredictionRecord)
        )
        row = result.first()
        return {
            "total_predictions": row[0] or 0,
            "avg_occupancy": round(row[1] or 0, 2),
            "max_occupancy": round(row[2] or 0, 2),
            "min_occupancy": round(row[3] or 0, 2)
        }

async def get_user_by_username(username: str) -> Optional[User]:
    async with async_session() as session:
        result = await session.execute(
            select(User).where(User.username == username)
        )
        return result.scalar_one_or_none()

async def create_user(username: str, password_hash: str, role: str = "user") -> User:
    async with async_session() as session:
        async with session.begin():
            user = User(username=username, password_hash=password_hash, role=role)
            session.add(user)
            await session.commit()
            await session.refresh(user)
            return user
