"""Cache facade over Redis with a bounded in-process fallback.

The fallback has to behave like Redis, because "Redis is down" is a routine
operational event rather than an exotic one. The previous fallback stored
``key -> payload`` and dropped the TTL on the floor, which meant every value
silently became permanent: with Redis unavailable the live-crowd snapshot was
computed once and then served unchanged for the life of the process, so the
"live" dashboard froze and ``last_updated`` stopped moving. Nothing logged the
degradation either. Entries here therefore carry an explicit expiry and the dict
is size-capped so a long-running process cannot grow without bound.
"""

import json
import logging
import time
from typing import Any, Optional

import redis

from app.core.config import settings

logger = logging.getLogger(__name__)

_redis_client: Optional[redis.Redis] = None
# key -> (monotonic_expiry, serialised payload)
_local_cache: dict[str, tuple[float, str]] = {}
_LOCAL_CACHE_MAX = 4096
_REDIS_FAILED_AT: float = 0.0
_REDIS_RETRY_COOLDOWN = 60.0


def get_redis() -> Optional[redis.Redis]:
    global _redis_client, _REDIS_FAILED_AT
    if _redis_client is not None:
        return _redis_client

    if not settings.REDIS_URL:
        return None
    if time.monotonic() - _REDIS_FAILED_AT < _REDIS_RETRY_COOLDOWN:
        return None
    try:
        client = redis.from_url(settings.REDIS_URL, decode_responses=True, socket_connect_timeout=2)
        client.ping()
        _redis_client = client
        logger.info("Connected to Redis")
        return client
    except Exception as e:
        _REDIS_FAILED_AT = time.monotonic()
        logger.warning(f"Redis unavailable ({e}); using in-memory cache for {_REDIS_RETRY_COOLDOWN:.0f}s")
        return None


def _local_set(key: str, payload: str, ttl: int) -> None:
    now = time.monotonic()
    if ttl <= 0:
        _local_cache.pop(key, None)
        return
    if len(_local_cache) >= _LOCAL_CACHE_MAX:
        expired = [k for k, (exp, _) in _local_cache.items() if exp <= now]
        for k in expired:
            _local_cache.pop(k, None)
        # Still full of live entries: evict oldest first (dict preserves order).
        while len(_local_cache) >= _LOCAL_CACHE_MAX:
            _local_cache.pop(next(iter(_local_cache)), None)
    _local_cache[key] = (now + ttl, payload)


def _local_get(key: str) -> Optional[str]:
    entry = _local_cache.get(key)
    if entry is None:
        return None
    expires_at, payload = entry
    if expires_at <= time.monotonic():
        _local_cache.pop(key, None)
        return None
    return payload


def cache_set(key: str, value: Any, ttl: int = 300) -> None:
    r = get_redis()
    payload = json.dumps(value, default=str)
    if r is not None:
        try:
            r.setex(key, ttl, payload)
            return
        except Exception as e:
            # Fail open into the local cache rather than losing the write, and fall
            # back for a cooldown so a dead Redis is not probed on every request.
            global _REDIS_FAILED_AT
            _REDIS_FAILED_AT = time.monotonic()
            _redis_client = None
            logger.warning(f"Redis write failed ({e}); caching in-process instead")
    _local_set(key, payload, ttl)


def cache_get(key: str) -> Optional[Any]:
    r = get_redis()
    if r is not None:
        try:
            payload = r.get(key)
        except Exception as e:
            global _REDIS_FAILED_AT
            _REDIS_FAILED_AT = time.monotonic()
            logger.warning(f"Redis read failed ({e}); serving from in-process cache")
            payload = _local_get(key)
    else:
        payload = _local_get(key)
    if payload is None:
        return None
    try:
        return json.loads(payload)
    except Exception:
        return payload


def cache_delete(key: str) -> None:
    r = get_redis()
    if r is not None:
        try:
            r.delete(key)
        except Exception as e:
            logger.warning(f"Redis delete failed ({e}); deleting in-process entry only")
    _local_cache.pop(key, None)


def cache_clear_local() -> None:
    """Test helper: drop every in-process entry."""
    _local_cache.clear()
