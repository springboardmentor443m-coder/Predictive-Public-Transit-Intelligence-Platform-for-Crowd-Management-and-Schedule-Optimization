import logging
import time
from typing import Any, Optional

from pymongo import MongoClient

from app.core.config import settings

logger = logging.getLogger(__name__)

_mongo_client: Optional[MongoClient] = None
_mongo_failed_at: float = 0.0
_MONGO_RETRY_COOLDOWN = 60.0


def get_mongo() -> Optional[Any]:
    global _mongo_client, _mongo_failed_at
    if _mongo_client is not None:
        return _mongo_client

    if not settings.MONGODB_URL:
        return None
    if time.monotonic() - _mongo_failed_at < _MONGO_RETRY_COOLDOWN:
        return None
    try:
        client = MongoClient(settings.MONGODB_URL, serverSelectionTimeoutMS=2000)
        client.admin.command("ping")
        _mongo_client = client
        logger.info("Connected to MongoDB")
        return client
    except Exception as e:
        _mongo_failed_at = time.monotonic()
        logger.warning(f"MongoDB unavailable ({e}); sensor data storage disabled for {_MONGO_RETRY_COOLDOWN:.0f}s")
        return None


def get_sensor_events_collection():
    mongo = get_mongo()
    if mongo is None:
        return None
    return mongo["metroflow"]["sensor_events"]


def insert_sensor_event(event: dict) -> Optional[str]:
    coll = get_sensor_events_collection()
    if coll is None:
        return None
    res = coll.insert_one(event)
    return str(res.inserted_id)
