import logging
from typing import AsyncGenerator
from sqlalchemy.ext.asyncio import AsyncSession, create_async_engine, async_sessionmaker
from sqlalchemy.orm import declarative_base

from app.core.config import settings

logger = logging.getLogger("metroflow.database")

# SQLAlchemy setup
async_engine = create_async_engine(
    settings.DATABASE_URL,
    echo=False,
    future=True,
)

AsyncSessionLocal = async_sessionmaker(
    async_engine, class_=AsyncSession, expire_on_commit=False
)

Base = declarative_base()


async def get_db() -> AsyncGenerator[AsyncSession, None]:
    async with AsyncSessionLocal() as session:
        try:
            yield session
            await session.commit()
        except Exception:
            await session.rollback()
            raise
        finally:
            await session.close()


# MongoDB (Motor) setup with safety fallback
mongo_client = None
mongo_db = None

try:
    from motor.motor_asyncio import AsyncIOMotorClient
    mongo_client = AsyncIOMotorClient(settings.MONGODB_URL, serverSelectionTimeoutMS=2000)
    mongo_db = mongo_client[settings.MONGODB_DB_NAME]
except Exception as e:
    logger.warning(f"MongoDB connection initialization skipped: {e}")


# Redis setup with safety fallback
class MockRedis:
    """In-memory Redis fallback if real Redis instance is not available locally."""
    def __init__(self):
        self.store = {}

    async def get(self, key: str):
        return self.store.get(key)

    async def set(self, key: str, value: str, ex: int = None):
        self.store[key] = value
        return True

    async def hgetall(self, name: str):
        return self.store.get(name, {})

    async def hset(self, name: str, key: str = None, value: str = None, mapping: dict = None):
        if name not in self.store:
            self.store[name] = {}
        if mapping:
            self.store[name].update(mapping)
        elif key:
            self.store[name][key] = value
        return True

    async def publish(self, channel: str, message: str):
        return 1


redis_client = None

try:
    import redis.asyncio as aioredis
    redis_client = aioredis.from_url(settings.REDIS_URL, decode_responses=True)
except Exception:
    redis_client = MockRedis()


async def get_redis():
    return redis_client
