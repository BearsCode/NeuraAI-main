from __future__ import annotations

from datetime import UTC, datetime
from enum import IntEnum

from fastapi import HTTPException, Request, status
from redis.asyncio import Redis

from backend.app.core.configs import settings
from backend.app.db.user import User


class AnomalyLevel(IntEnum):
    NORMAL = 0
    WARNING = 1
    CRITICAL = 2
    DANGER = 3


class AnomalyScore:
    def __init__(self) -> None:
        self.level: AnomalyLevel = AnomalyLevel.NORMAL
        self.reasons: list[str] = []

    def add(self, level: AnomalyLevel, reason: str) -> None:
        if level > self.level:
            self.level = level
        self.reasons.append(reason)


async def analyze_login_anomaly(
    redis: Redis | None,
    user: User,
    ip_address: str | None,
) -> AnomalyScore:
    score = AnomalyScore()

    if redis is None:
        return score

    if ip_address:
        ip_key = f"anomaly:ip:{user.id}:{ip_address}"
        seen = await redis.get(ip_key)
        if seen is None:
            from_another = await redis.get(f"anomaly:known-ips:{user.id}")
            if from_another:
                score.add(AnomalyLevel.WARNING, "Login from new IP address")

    if await _is_unusual_time():
        score.add(AnomalyLevel.WARNING, "Login during unusual hours (2-6 AM)")

    if user.last_login_at:
        hours_since_last = (datetime.now(UTC) - user.last_login_at).total_seconds() / 3600
        if hours_since_last > 720:
            score.add(AnomalyLevel.WARNING, "No login for over 30 days")

    return score


async def analyze_action_anomaly(
    redis: Redis | None,
    user: User,
    action: str,
) -> AnomalyScore:
    score = AnomalyScore()

    if redis is None:
        return score

    action_key = f"anomaly:actions:{user.id}:{datetime.now(UTC).strftime('%Y%m%d%H%M')}"
    count = await redis.incr(action_key)
    if count == 1:
        await redis.expire(action_key, 60)

    max_actions = settings.admin.anomaly_max_actions_per_minute
    if count > max_actions:
        score.add(AnomalyLevel.CRITICAL, f"Excessive actions: {count}/{max_actions} per minute")

    export_actions = {"export", "download", "bulk_export"}
    if any(a in action.lower() for a in export_actions):
        export_key = f"anomaly:exports:{user.id}:{datetime.now(UTC).strftime('%Y%m%d')}"
        export_count = await redis.incr(export_key)
        if export_count == 1:
            await redis.expire(export_key, 86400)
        if export_count > 5:
            score.add(AnomalyLevel.CRITICAL, "Excessive data exports today")

    return score


async def check_brute_force(
    redis: Redis | None,
    ip_address: str | None,
) -> bool:
    if redis is None or ip_address is None:
        return True

    blocked_key = f"brute:blocked:{ip_address}"
    blocked = await redis.get(blocked_key)
    if blocked:
        return False

    return True


async def record_login_attempt(
    redis: Redis | None,
    ip_address: str | None,
    success: bool,
) -> None:
    if redis is None or ip_address is None:
        return

    if success:
        await redis.delete(f"brute:attempts:{ip_address}")
        return

    key = f"brute:attempts:{ip_address}"
    pipe = redis.pipeline()
    pipe.incr(key)
    pipe.expire(key, settings.admin.brute_force_block_minutes * 60)
    results = await pipe.execute()
    attempts = int(results[0])

    if attempts >= settings.admin.brute_force_max_attempts:
        blocked_key = f"brute:blocked:{ip_address}"
        await redis.setex(blocked_key, settings.admin.brute_force_block_minutes * 60, "1")
        await redis.delete(key)

        block_count_key = f"brute:block-count:{ip_address}"
        block_count = await redis.incr(block_count_key)
        if block_count == 1:
            await redis.expire(block_count_key, 86400)
        if block_count >= 3:
            await redis.setex(blocked_key, settings.admin.brute_force_3_blocks_hours * 3600, "1")


async def handle_anomaly(
    request: Request,
    score: AnomalyScore,
) -> None:
    if score.level >= AnomalyLevel.DANGER:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Access blocked due to suspicious activity",
        )

    if score.level >= AnomalyLevel.CRITICAL:
        raise HTTPException(
            status_code=status.HTTP_428_PRECONDITION_REQUIRED,
            detail="Additional verification required. Check your email/SMS.",
        )


async def _is_unusual_time() -> bool:
    current_hour = datetime.now(UTC).hour
    start = settings.admin.anomaly_suspicious_hours_start
    end = settings.admin.anomaly_suspicious_hours_end
    if start <= end:
        return start <= current_hour <= end
    return current_hour >= start or current_hour <= end
