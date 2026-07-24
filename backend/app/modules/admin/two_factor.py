from __future__ import annotations

import secrets

from redis.asyncio import Redis

from backend.app.core.configs import settings
from backend.app.core.security import hash_email_otp


def generate_2fa_code() -> str:
    return f"{secrets.randbelow(1000000):06d}"


async def store_2fa_code(redis: Redis, user_id: str, code_hash: str) -> None:
    ttl = settings.admin.two_factor_code_ttl_seconds
    await redis.setex(f"2fa:code:{user_id}", ttl, code_hash)


async def verify_2fa_code(redis: Redis, user_id: str, code: str) -> bool:
    stored_hash = await redis.get(f"2fa:code:{user_id}")
    if stored_hash is None:
        return False
    computed_hash = hash_email_otp(user_id, code)
    if stored_hash.decode() != computed_hash:
        return False
    await redis.delete(f"2fa:code:{user_id}")
    return True


async def check_2fa_rate_limit(redis: Redis, user_id: str) -> tuple[bool, int | None]:
    key = f"2fa:attempts:{user_id}"
    blocked_key = f"2fa:blocked:{user_id}"

    blocked_ttl = await redis.ttl(blocked_key)
    if blocked_ttl > 0:
        return False, int(blocked_ttl)

    attempts = await redis.get(key)
    if attempts is not None and int(attempts) >= settings.admin.two_factor_max_attempts:
        block_minutes = settings.admin.two_factor_block_minutes
        await redis.setex(blocked_key, block_minutes * 60, "1")
        await redis.delete(key)
        return False, block_minutes * 60

    return True, None


async def increment_2fa_attempts(redis: Redis, user_id: str) -> int:
    key = f"2fa:attempts:{user_id}"
    pipe = redis.pipeline()
    pipe.incr(key)
    pipe.expire(key, settings.admin.two_factor_block_minutes * 60)
    results = await pipe.execute()
    return int(results[0])


async def reset_2fa_attempts(redis: Redis, user_id: str) -> None:
    pipe = redis.pipeline()
    pipe.delete(f"2fa:attempts:{user_id}")
    pipe.delete(f"2fa:blocked:{user_id}")
    pipe.delete(f"2fa:code:{user_id}")
    await pipe.execute()


async def can_resend_2fa(redis: Redis, user_id: str) -> bool:
    key = f"2fa:resend:{user_id}"
    count = await redis.get(key)
    if count is not None and int(count) >= settings.admin.two_factor_resend_limit:
        return False
    pipe = redis.pipeline()
    pipe.incr(key)
    pipe.expire(key, settings.admin.two_factor_resend_window_seconds)
    await pipe.execute()
    return True
