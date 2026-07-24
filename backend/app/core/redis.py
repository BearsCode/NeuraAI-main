from __future__ import annotations

from functools import lru_cache

from redis.asyncio import ConnectionPool, Redis

from backend.app.core.configs import settings


@lru_cache(maxsize=1)
def _redis_pool() -> ConnectionPool:
    return ConnectionPool.from_url(
        settings.redis_url,
        encoding="utf-8",
        decode_responses=True,
        max_connections=50,
        socket_keepalive=True,
        socket_connect_timeout=5,
        socket_timeout=5,
        retry_on_timeout=True,
    )


@lru_cache
def get_redis_client() -> Redis:
    return Redis.from_pool(_redis_pool())
