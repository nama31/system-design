import redis

from config import settings


class CacheClient:
    def __init__(self, redis_url: str | None = None, ttl_seconds: int | None = None):
        self._client = redis.Redis.from_url(redis_url or settings.redis_url, decode_responses=True)
        self._ttl_seconds = ttl_seconds or settings.cache_ttl_seconds

    def get(self, key: str) -> str | None:
        return self._client.get(key)

    def set(self, key: str, value: str) -> None:
        self._client.setex(key, self._ttl_seconds, value)
