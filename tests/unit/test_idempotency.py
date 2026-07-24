from __future__ import annotations

from pydantic import BaseModel
import pytest
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker, create_async_engine

from backend.app.db.base import Base
from backend.app.db.enums import UserRole
from backend.app.db.user import User
from backend.app.infra.idempotency import IdempotencyContext, IdempotencyService


class DemoResponse(BaseModel):
    resource_id: str
    status: str


@pytest.mark.asyncio
async def test_idempotency_replays_previous_response() -> None:
    engine = create_async_engine("sqlite+aiosqlite:///:memory:")
    async with engine.begin() as connection:
        await connection.run_sync(Base.metadata.create_all)

    session_factory = async_sessionmaker(engine, class_=AsyncSession, expire_on_commit=False)
    async with session_factory() as session:
        user = User(
            email="idempotency@example.com",
            password_hash="hashed",
            full_name="Idempotency User",
            role=UserRole.CLIENT,
            is_active=True,
        )
        session.add(user)
        await session.commit()

        service = IdempotencyService()
        context = IdempotencyContext(
            tenant_id="tenant-1",
            user_id=user.id,
            endpoint="/api/v1/content-plans",
            key="same-request",
            request_body={"period_days": 30},
        )

        first = await service.execute(
            session=session,
            context=context,
            operation=lambda: _build_response("plan-1"),
            serializer=lambda payload: payload.model_dump(mode="json"),
            deserializer=DemoResponse.model_validate,
        )
        await session.commit()

        second = await service.execute(
            session=session,
            context=context,
            operation=lambda: _build_response("plan-2"),
            serializer=lambda payload: payload.model_dump(mode="json"),
            deserializer=DemoResponse.model_validate,
        )

        assert first.replayed is False
        assert second.replayed is True
        assert second.value.resource_id == "plan-1"

    await engine.dispose()


async def _build_response(resource_id: str) -> DemoResponse:
    return DemoResponse(resource_id=resource_id, status="created")
