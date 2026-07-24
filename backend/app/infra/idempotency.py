from __future__ import annotations

import json
from collections.abc import Awaitable, Callable
from dataclasses import dataclass
from hashlib import sha256
from typing import Any, Generic, TypeVar

from fastapi import HTTPException, status
from sqlalchemy import select
from sqlalchemy.exc import IntegrityError
from sqlalchemy.ext.asyncio import AsyncSession

from backend.app.db.enums import IdempotencyStatus
from backend.app.db.idempotency_key import IdempotencyKey

ResultT = TypeVar("ResultT")


@dataclass(frozen=True)
class IdempotencyContext:
    tenant_id: str
    user_id: str
    endpoint: str
    key: str
    request_body: dict[str, Any]


@dataclass(frozen=True)
class IdempotencyResult(Generic[ResultT]):
    value: ResultT
    replayed: bool = False


class IdempotencyService:
    async def execute(
        self,
        session: AsyncSession,
        context: IdempotencyContext,
        operation: Callable[[], Awaitable[ResultT]],
        serializer: Callable[[ResultT], dict[str, Any]],
        deserializer: Callable[[dict[str, Any]], ResultT],
    ) -> IdempotencyResult[ResultT]:
        payload_hash = self._hash_payload(context.request_body)
        record = await session.scalar(
            select(IdempotencyKey).where(
                IdempotencyKey.tenant_id == context.tenant_id,
                IdempotencyKey.user_id == context.user_id,
                IdempotencyKey.endpoint == context.endpoint,
                IdempotencyKey.idempotency_key == context.key,
            )
        )
        if record:
            if record.request_hash != payload_hash:
                raise HTTPException(
                    status_code=status.HTTP_409_CONFLICT,
                    detail="Idempotency key payload mismatch",
                )
            if not record.response_json:
                raise HTTPException(
                    status_code=status.HTTP_409_CONFLICT,
                    detail="Idempotent request is already in progress",
                )
            return IdempotencyResult(
                value=deserializer(json.loads(record.response_json)),
                replayed=True,
            )

        record = IdempotencyKey(
            tenant_id=context.tenant_id,
            user_id=context.user_id,
            endpoint=context.endpoint,
            idempotency_key=context.key,
            request_hash=payload_hash,
        )
        session.add(record)
        try:
            await session.flush()
        except IntegrityError:
            await session.rollback()
            existing = await session.scalar(
                select(IdempotencyKey).where(
                    IdempotencyKey.tenant_id == context.tenant_id,
                    IdempotencyKey.user_id == context.user_id,
                    IdempotencyKey.endpoint == context.endpoint,
                    IdempotencyKey.idempotency_key == context.key,
                )
            )
            if existing and existing.status == IdempotencyStatus.IN_PROGRESS:
                raise HTTPException(
                    status_code=status.HTTP_409_CONFLICT,
                    detail="Idempotent request is already in progress",
                )
            raise

        result = await operation()
        record.status = IdempotencyStatus.COMPLETED
        record.response_json = json.dumps(serializer(result), default=str)
        return IdempotencyResult(value=result)

    def _hash_payload(self, payload: dict[str, Any]) -> str:
        encoded = json.dumps(payload, sort_keys=True, default=str).encode("utf-8")
        return sha256(encoded).hexdigest()
