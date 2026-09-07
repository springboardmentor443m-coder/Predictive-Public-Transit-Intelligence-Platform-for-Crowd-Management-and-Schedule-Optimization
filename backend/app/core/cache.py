import json
import logging
import time
from typing import Any, Optional

import redis

from app.core.config import settings

logger = logging.getLogger(__name__)

_redis_client: Optional[redis.Redis] = None
_local_cache: dict[str, str] = {}
_redis_failed_at: float = 0.0
_REDIS_RETRY_COOLDOWN = 60.0


def get_redis() -> Optional[redis.Redis]:
    global _redis_client, _redis_failed_at
    if _redis_client is not None:
        return _redis_client

    if not settings.REDIS_URL:
        return None
    if time.monotonic() - _redis_failed_at < _REDIS_RETRY_COOLDOWN:
        return None
    try:
        client = redis.from_url(settings.REDIS_URL, decode_responses=True, socket_connect_timeout=2)
        client.ping()
        _redis_client = client
        logger.info("Connected to Redis")
        return client
    except Exception as e:
        _redis_failed_at = time.monotonic()
        logger.warning(f"Redis unavailable ({e}); using in-memory cache for {_REDIS_RETRY_COOLDOWN:.0f}s")
        return None


def cache_set(key: str, value: Any, ttl: int = 300) -> None:
    r = get_redis()
    payload = json.dumps(value, default=str)
    if r is not None:
        r.setex(key, ttl, payload)
    else:
        _local_cache[key] = payload


def cache_get(key: str) -> Optional[Any]:
    r = get_redis()
    if r is not None:
        payload = r.get(key)
    else:
        payload = _local_cache.get(key)
    if payload is None:
        return None
    try:
        return json.loads(payload)
    except Exception:
        return payload


def cache_delete(key: str) -> None:
    r = get_redis()
    if r is not None:
        r.delete(key)
    _local_cache.pop(key, None)
