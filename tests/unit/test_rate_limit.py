from __future__ import annotations

import pytest
from fastapi import HTTPException
from fakeredis.aioredis import FakeRedis

from backend.app.infra.rate_limit import RateLimitContext, RateLimiter


@pytest.mark.asyncio
async def test_rate_limiter_blocks_after_limit() -> None:
    redis = FakeRedis(decode_responses=True)
    limiter = RateLimiter(redis)
    context = RateLimitContext(actor_key="user-1", endpoint="/api/v1/publishing", limit=2, window_seconds=60)

    await limiter.enforce(context)
    await limiter.enforce(context)

    with pytest.raises(HTTPException) as exc_info:
        await limiter.enforce(context)

    assert exc_info.value.status_code == 429
    await redis.aclose()
