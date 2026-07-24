from __future__ import annotations

import asyncio
from datetime import UTC, datetime
from pathlib import Path

import boto3
from fastapi import APIRouter, Request
from redis.exceptions import RedisError

from backend.app.core.database import check_database_connection
from backend.app.core.configs import settings
from backend.app.schemas.health import HealthComponentResponse, HealthResponse

router = APIRouter(prefix="/health", tags=["health"])


@router.get("/live", response_model=HealthResponse)
async def liveness() -> HealthResponse:
    return HealthResponse(
        status="ok",
        service=settings.app.name,
        environment=settings.app.env,
        version=settings.app.version,
        timestamp=datetime.now(UTC),
    )


@router.get("/ready", response_model=HealthResponse)
@router.get("", response_model=HealthResponse)
async def readiness(request: Request) -> HealthResponse:
    components: list[HealthComponentResponse] = []

    database_ok, database_detail = await check_database_connection()
    components.append(
        HealthComponentResponse(
            name="database",
            status="ok" if database_ok else "down",
            details=database_detail,
        )
    )

    redis_ok, redis_details = await _check_redis(request)
    components.append(
        HealthComponentResponse(
            name="queue",
            status="ok" if redis_ok else "degraded",
            details=redis_details,
        )
    )

    storage_ok, storage_details = await _check_storage()
    components.append(
        HealthComponentResponse(
            name="storage",
            status="ok" if storage_ok else "degraded",
            details=storage_details,
        )
    )

    ai_ok, ai_details = _check_ai()
    components.append(
        HealthComponentResponse(
            name="ai",
            status="ok" if ai_ok else "degraded",
            details=ai_details,
        )
    )

    statuses = {component.status for component in components}
    overall_status = "down" if "down" in statuses else ("degraded" if "degraded" in statuses else "ok")
    return HealthResponse(
        status=overall_status,
        service=settings.app.name,
        environment=settings.app.env,
        version=settings.app.version,
        timestamp=datetime.now(UTC),
        components=components,
    )


async def _check_redis(request: Request) -> tuple[bool, dict[str, str]]:
    try:
        await request.app.state.redis.ping()
    except RedisError:
        return False, {
            "backend": "redis",
            "tls": str(settings.redis_uses_tls).lower(),
            "message": "connection failed",
        }
    return True, {
        "backend": "redis",
        "tls": str(settings.redis_uses_tls).lower(),
    }


async def _check_storage() -> tuple[bool, dict[str, str]]:
    if not settings.s3.endpoint_url:
        root = Path(settings.s3.local_root)
        root.mkdir(parents=True, exist_ok=True)
        return True, {"backend": "local", "mode": "filesystem"}

    try:
        client = boto3.client(
            "s3",
            endpoint_url=settings.s3.endpoint_url,
            aws_access_key_id=settings.s3.access_key_id.get_secret_value() if settings.s3.access_key_id else None,
            aws_secret_access_key=settings.s3.secret_access_key.get_secret_value() if settings.s3.secret_access_key else None,
            region_name=settings.s3.region,
        )
        await asyncio.to_thread(client.head_bucket, Bucket=settings.s3.bucket)
    except Exception:
        return False, {"backend": "s3", "bucket": settings.s3.bucket, "message": "bucket check failed"}
    return True, {"backend": "s3", "bucket": settings.s3.bucket}


def _check_ai() -> tuple[bool, dict[str, str]]:
    if settings.ai.provider == "mock":
        return True, {"provider": "mock", "mode": "fallback"}

    credentials = getattr(settings.ai, settings.ai.provider)
    if not credentials.api_key:
        return False, {"provider": settings.ai.provider, "message": "API key is not configured"}

    return True, {"provider": settings.ai.provider, "model": credentials.model or "default"}
