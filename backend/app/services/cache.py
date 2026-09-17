import json
import redis
from typing import Optional, Tuple
from app.core.config import settings


class CacheService:
    """
    Redis cache client with connection pooling and graceful error handling.
    Caches crowd predictions using key format: predict:{station_code}:{hour}:{day_of_week}
    """
    def __init__(self):
        self.client: Optional[redis.Redis] = None
        self._connected: bool = False

    def _get_client(self) -> Optional[redis.Redis]:
        if not self._connected:
            try:
                pool = redis.ConnectionPool.from_url(
                    settings.REDIS_URL,
                    decode_responses=True,
                    socket_timeout=1.0,
                    socket_connect_timeout=1.0,
                )
                r = redis.Redis(connection_pool=pool)
                r.ping()
                self.client = r
                print("[Redis] Connected successfully to Redis server.")
            except Exception as e:
                # Silently run in cache-miss mode when Redis is not running locally
                self.client = None
            self._connected = True
        return self.client

    def get_prediction(self, station_code: str, hour: int, day_of_week: int) -> Optional[Tuple[float, str]]:
        client = self._get_client()
        if not client:
            return None
        try:
            cache_key = f"predict:{station_code}:{hour}:{day_of_week}"
            data = self.client.get(cache_key)
            if data:
                payload = json.loads(data)
                return float(payload["predicted_density"]), str(payload["congestion_label"])
        except Exception as e:
            print(f"[Redis] Cache get error: {e}")
        return None

    def set_prediction(
        self,
        station_code: str,
        hour: int,
        day_of_week: int,
        predicted_density: float,
        congestion_label: str,
        ttl_seconds: int = 300,
    ) -> None:
        """
        Stores predicted density and label with a 5-minute (300s) TTL.
        """
        client = self._get_client()
        if not client:
            return
        try:
            cache_key = f"predict:{station_code}:{hour}:{day_of_week}"
            payload = json.dumps({
                "predicted_density": predicted_density,
                "congestion_label": congestion_label,
            })
            client.setex(cache_key, ttl_seconds, payload)
        except Exception as e:
            print(f"[Redis] Cache set error: {e}")


cache_service = CacheService()
