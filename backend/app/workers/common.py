from __future__ import annotations

import asyncio
from typing import Any
from urllib.parse import urlparse

from arq.connections import RedisSettings

from backend.app.core.database import get_session_factory
from backend.app.core.redis import get_redis_client
from backend.app.core.configs import settings
from backend.app.events.bus import RedisEventBus
from backend.app.integrations.ai_adapters import build_ai_adapter
from backend.app.integrations.social_adapters import SocialAdapterRegistry

WorkerContext = dict[str, Any]


def build_redis_settings() -> RedisSettings:
    parsed = urlparse(settings.redis_url)
    database = int(parsed.path.lstrip("/") or "0")
    return RedisSettings(
        host=parsed.hostname or "localhost",
        port=parsed.port or 6379,
        database=database,
        username=parsed.username,
        password=parsed.password,
        ssl=parsed.scheme == "rediss",
    )


async def startup(ctx: WorkerContext) -> None:
    redis = get_redis_client()
    ctx["redis"] = redis
    ctx["session_factory"] = get_session_factory()
    ctx["event_bus"] = RedisEventBus(redis)
    ctx["ai_adapter"] = build_ai_adapter()
    ctx["social_registry"] = SocialAdapterRegistry()
    ctx["platform_semaphores"] = {
        "telegram": asyncio.Semaphore(max(1, settings.social.telegram.rate_limit_per_minute // 30)),
        "vk": asyncio.Semaphore(max(1, settings.social.vk.rate_limit_per_minute // 30)),
    }


async def shutdown(ctx: WorkerContext) -> None:
    redis = ctx.get("redis")
    if redis is not None:
        await redis.aclose()
