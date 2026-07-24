from __future__ import annotations

from dataclasses import dataclass

from fastapi import HTTPException, status
from redis.asyncio import Redis

from backend.app.core.configs import settings


@dataclass(frozen=True)
class RateLimitContext:
    actor_key: str
    endpoint: str
    limit: int
    window_seconds: int = 60


LUA_SLIDING_WINDOW = """
local key = KEYS[1]
local limit = tonumber(ARGV[1])
local window = tonumber(ARGV[2])
local now = tonumber(ARGV[3])
local clear_before = now - window

redis.call('ZREMRANGEBYSCORE', key, 0, clear_before)
local current_count = redis.call('ZCARD', key)

if current_count < limit then
    redis.call('ZADD', key, now, now)
    redis.call('EXPIRE', key, math.ceil(window / 1000))
    return 0
else
    local oldest = redis.call('ZRANGE', key, 0, 0, 'WITHSCORES')
    if oldest and oldest[2] then
        return (tonumber(oldest[2]) + window) - now
    else
        return window
    end
end
"""

class RateLimiter:
    def __init__(self, redis: Redis) -> None:
        self.redis = redis
        self.script = self.redis.register_script(LUA_SLIDING_WINDOW)

    async def enforce(self, context: RateLimitContext) -> None:
        import time
        redis_key = f"rate-limit:{context.endpoint}:{context.actor_key}:{context.window_seconds}"
        now_ms = int(time.time() * 1000)
        window_ms = context.window_seconds * 1000
        
        wait_ms = await self.script(keys=[redis_key], args=[context.limit, window_ms, now_ms])
        if wait_ms > 0:
            raise HTTPException(
                status_code=status.HTTP_429_TOO_MANY_REQUESTS,
                detail="Rate limit exceeded",
            )

class OutboundRateLimiter:
    def __init__(self, redis: Redis) -> None:
        self.redis = redis
        self.script = self.redis.register_script(LUA_SLIDING_WINDOW)
        
    async def wait_for_token(self, key: str, limit: int, window_seconds: int) -> None:
        import asyncio
        import time
        while True:
            now_ms = int(time.time() * 1000)
            window_ms = window_seconds * 1000
            wait_ms = await self.script(keys=[key], args=[limit, window_ms, now_ms])
            if wait_ms == 0:
                break
            await asyncio.sleep(wait_ms / 1000.0)

    def limit_for_role(self, role: str) -> int:
        if role == "admin":
            return settings.rate_limit.admin_requests_per_minute
        if role == "partner":
            return settings.rate_limit.partner_requests_per_minute
        return settings.rate_limit.client_requests_per_minute
