"""Redis connection and caching utilities."""

import json
from typing import Any, Optional
import redis.asyncio as aioredis
from redis import Redis
from app.core.config import settings


# Async Redis client (for FastAPI)
async_redis_client: Optional[aioredis.Redis] = None

# Sync Redis client (for Celery workers)
sync_redis_client: Optional[Redis] = None


async def get_redis() -> aioredis.Redis:
    """
    Get async Redis client instance.

    Returns:
        aioredis.Redis: Async Redis client
    """
    global async_redis_client
    if async_redis_client is None:
        async_redis_client = await aioredis.from_url(
            settings.REDIS_URL,
            encoding="utf-8",
            decode_responses=True,
        )
    return async_redis_client


def get_sync_redis() -> Redis:
    """
    Get sync Redis client instance (for workers).

    Returns:
        Redis: Sync Redis client
    """
    global sync_redis_client
    if sync_redis_client is None:
        sync_redis_client = Redis.from_url(
            settings.REDIS_URL,
            decode_responses=True,
        )
    return sync_redis_client


async def close_redis() -> None:
    """Close Redis connections."""
    global async_redis_client
    if async_redis_client:
        await async_redis_client.close()
        async_redis_client = None


class RedisCache:
    """Redis caching utility with async support."""

    def __init__(self, prefix: str = "cache"):
        """
        Initialize cache with key prefix.

        Args:
            prefix: Key prefix for namespacing
        """
        self.prefix = prefix

    def _make_key(self, key: str) -> str:
        """Create prefixed cache key."""
        return f"{self.prefix}:{key}"

    async def get(self, key: str) -> Optional[Any]:
        """
        Get value from cache.

        Args:
            key: Cache key

        Returns:
            Cached value or None
        """
        redis = await get_redis()
        value = await redis.get(self._make_key(key))
        if value:
            try:
                return json.loads(value)
            except json.JSONDecodeError:
                return value
        return None

    async def set(self, key: str, value: Any, expire: int = 3600) -> bool:
        """
        Set value in cache.

        Args:
            key: Cache key
            value: Value to cache
            expire: Expiration time in seconds

        Returns:
            True if successful
        """
        redis = await get_redis()
        serialized = json.dumps(value) if not isinstance(value, str) else value
        return await redis.setex(self._make_key(key), expire, serialized)

    async def delete(self, key: str) -> bool:
        """
        Delete key from cache.

        Args:
            key: Cache key

        Returns:
            True if key was deleted
        """
        redis = await get_redis()
        return await redis.delete(self._make_key(key)) > 0

    async def exists(self, key: str) -> bool:
        """
        Check if key exists in cache.

        Args:
            key: Cache key

        Returns:
            True if key exists
        """
        redis = await get_redis()
        return await redis.exists(self._make_key(key)) > 0
