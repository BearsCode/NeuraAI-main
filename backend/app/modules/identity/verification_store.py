from __future__ import annotations

import asyncio
from dataclasses import dataclass
from datetime import UTC, datetime, timedelta

from redis.asyncio import Redis
from redis.exceptions import RedisError


@dataclass(slots=True)
class VerificationCodeRecord:
    """Verification code state stored in Redis or a fallback cache."""

    user_id: str
    code_hash: str
    attempts: int
    expires_at: datetime


class VerificationCodeStore:
    """Redis-backed OTP store with an in-memory fallback for local runs."""

    _fallback_data: dict[str, VerificationCodeRecord] = {}
    _fallback_lock = asyncio.Lock()

    def __init__(self, redis: Redis | None) -> None:
        self.redis = redis

    async def save(self, email: str, record: VerificationCodeRecord, ttl_seconds: int) -> None:
        """Persist a verification code with TTL."""

        redis_key = self._redis_key(email)
        if self.redis is not None:
            try:
                await self.redis.hset(
                    redis_key,
                    mapping={
                        "user_id": record.user_id,
                        "code_hash": record.code_hash,
                        "attempts": str(record.attempts),
                        "expires_at": record.expires_at.isoformat(),
                    },
                )
                await self.redis.expire(redis_key, ttl_seconds)
                return
            except RedisError:
                pass

        async with self._fallback_lock:
            self._fallback_data[redis_key] = record

    async def get(self, email: str) -> VerificationCodeRecord | None:
        """Fetch the verification state for an email."""

        redis_key = self._redis_key(email)
        if self.redis is not None:
            try:
                payload = await self.redis.hgetall(redis_key)
                if payload:
                    return VerificationCodeRecord(
                        user_id=payload["user_id"],
                        code_hash=payload["code_hash"],
                        attempts=int(payload["attempts"]),
                        expires_at=datetime.fromisoformat(payload["expires_at"]).astimezone(UTC),
                    )
            except RedisError:
                pass

        async with self._fallback_lock:
            record = self._fallback_data.get(redis_key)
            if record and record.expires_at > datetime.now(UTC):
                return record
            self._fallback_data.pop(redis_key, None)
            return None

    async def increment_attempts(self, email: str) -> VerificationCodeRecord | None:
        """Increment verification attempts and return updated state."""

        record = await self.get(email)
        if record is None:
            return None

        updated = VerificationCodeRecord(
            user_id=record.user_id,
            code_hash=record.code_hash,
            attempts=record.attempts + 1,
            expires_at=record.expires_at,
        )
        ttl_seconds = max(int((record.expires_at - datetime.now(UTC)).total_seconds()), 1)
        await self.save(email, updated, ttl_seconds)
        return updated

    async def delete(self, email: str) -> None:
        """Delete the OTP state for an email."""

        redis_key = self._redis_key(email)
        if self.redis is not None:
            try:
                await self.redis.delete(redis_key)
                return
            except RedisError:
                pass

        async with self._fallback_lock:
            self._fallback_data.pop(redis_key, None)

    async def ttl(self, email: str, default_seconds: int) -> int:
        """Return the remaining TTL for an email code."""

        redis_key = self._redis_key(email)
        if self.redis is not None:
            try:
                ttl_value = await self.redis.ttl(redis_key)
                if ttl_value and ttl_value > 0:
                    return ttl_value
            except RedisError:
                pass

        async with self._fallback_lock:
            record = self._fallback_data.get(redis_key)
            if record is None:
                return default_seconds
            return max(int((record.expires_at - datetime.now(UTC)).total_seconds()), 1)

    def build_record(self, user_id: str, code_hash: str, ttl_seconds: int) -> VerificationCodeRecord:
        """Create a record with the expected expiration."""

        return VerificationCodeRecord(
            user_id=user_id,
            code_hash=code_hash,
            attempts=0,
            expires_at=datetime.now(UTC) + timedelta(seconds=ttl_seconds),
        )

    def _redis_key(self, email: str) -> str:
        return f"auth:email-verification:{email.strip().lower()}"
