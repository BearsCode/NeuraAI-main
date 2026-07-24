from __future__ import annotations

import pickle
from typing import Any, TypeVar

from redis.asyncio import Redis

from backend.app.core.configs import settings
from backend.app.core.redis import get_redis_client
from backend.app.observability.logging import get_logger

T = TypeVar("T")

logger = get_logger(__name__)


class CacheService:
    """Generic Redis-backed cache with TTL, safe serialization, and graceful degradation."""

    PREFIX = "cache:v1:"

    def __init__(self, redis: Redis | None = None) -> None:
        self._redis = redis

    async def _client(self) -> Redis:
        if self._redis is None:
            self._redis = get_redis_client()
        return self._redis

    def _key(self, namespace: str, key: str) -> str:
        return f"{self.PREFIX}{namespace}:{key}"

    async def get(self, namespace: str, key: str) -> Any | None:
        try:
            r = await self._client()
            raw = await r.get(self._key(namespace, key))
            if raw is not None:
                return pickle.loads(raw)
        except Exception as exc:
            logger.warning("cache_get_error", namespace=namespace, key=key, error=str(exc))
        return None

    async def set(
        self,
        namespace: str,
        key: str,
        value: Any,
        ttl_seconds: int | None = None,
    ) -> None:
        try:
            r = await self._client()
            ttl = ttl_seconds or settings.redis.cache_ttl_seconds
            await r.setex(self._key(namespace, key), ttl, pickle.dumps(value))
        except Exception as exc:
            logger.warning("cache_set_error", namespace=namespace, key=key, error=str(exc))

    async def delete(self, namespace: str, key: str) -> None:
        try:
            r = await self._client()
            await r.delete(self._key(namespace, key))
        except Exception as exc:
            logger.warning("cache_delete_error", namespace=namespace, key=key, error=str(exc))

    async def invalidate_namespace(self, namespace: str) -> None:
        try:
            r = await self._client()
            cursor = 0
            pattern = f"{self.PREFIX}{namespace}:*"
            while True:
                cursor, keys = await r.scan(cursor, match=pattern, count=100)
                if keys:
                    await r.delete(*keys)
                if cursor == 0:
                    break
        except Exception as exc:
            logger.warning("cache_invalidate_error", namespace=namespace, error=str(exc))

    async def get_or_set(
        self,
        namespace: str,
        key: str,
        factory: Any,
        ttl_seconds: int | None = None,
    ) -> Any:
        cached = await self.get(namespace, key)
        if cached is not None:
            return cached
        value = await factory() if callable(factory) else factory
        await self.set(namespace, key, value, ttl_seconds)
        return value
