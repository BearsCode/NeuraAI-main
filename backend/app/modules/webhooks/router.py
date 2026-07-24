from __future__ import annotations

import asyncio
import hashlib
import hmac
import json
import logging
from datetime import UTC, datetime
from typing import Any

from fastapi import APIRouter, Header, HTTPException, Request
from pydantic import BaseModel

from backend.app.core.configs import settings
from backend.app.core.redis import get_redis_client
from backend.app.modules.ai_core.state_manager import StateManager

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/webhooks", tags=["webhooks"])

_IDEMPOTENCY_TTL = 300
_MAX_BODY_BYTES = 1 * 1024 * 1024
_MAX_WEBHOOK_AGE_SECONDS = 300


class WebhookPayload(BaseModel):
    event: str
    data: dict[str, Any]


_webhook_background_tasks: set[asyncio.Task] = set()


def _verify_signature(
    payload: bytes,
    signature: str | None,
    secret_value: str,
) -> bool:
    if not signature:
        return False
    expected = hmac.new(
        secret_value.encode(),
        payload,
        hashlib.sha256,
    ).hexdigest()
    return hmac.compare_digest(signature, expected)


def _verify_heygen_signature(payload: bytes, signature: str | None) -> bool:
    secret = settings.avatar.heygen.webhook_secret
    if not secret:
        logger.warning("heygen_webhook_secret_not_configured")
        return False
    return _verify_signature(payload, signature, secret.get_secret_value())


def _verify_replicate_signature(payload: bytes, signature: str | None) -> bool:
    secret = settings.avatar.replicate.webhook_secret
    if not secret:
        logger.warning("replicate_webhook_secret_not_configured")
        return False
    return _verify_signature(payload, signature, secret.get_secret_value())


async def _is_duplicate(webhook_id: str) -> bool:
    redis = get_redis_client()
    key = f"webhook:idempotent:{webhook_id}"
    existed = await redis.set(key, "1", nx=True, ex=_IDEMPOTENCY_TTL)
    return not bool(existed)


async def _process_webhook(job_id: str, result: dict[str, Any]) -> None:
    try:
        state_manager = StateManager()
        from backend.app.core.database import get_db_session

        async for session in get_db_session():
            try:
                step = await state_manager.get_step_by_job(session, job_id)
                if step:
                    await state_manager.update_step_result(
                        session,
                        step_id=step.id,
                        result=result,
                    )
            finally:
                await session.close()
    except Exception:
        logger.exception("webhook_processing_failed job_id=%s", job_id)


def _fire_background_job(job_id: str, result: dict[str, Any]) -> None:
    task = asyncio.create_task(_process_webhook(job_id, result))
    _webhook_background_tasks.add(task)
    task.add_done_callback(_webhook_background_tasks.discard)


@router.post("/heygen")
async def heygen_webhook(
    request: Request,
    x_heygen_signature: str | None = Header(None),
) -> dict[str, str]:
    body_bytes = await request.body()
    if len(body_bytes) > _MAX_BODY_BYTES:
        raise HTTPException(status_code=413, detail="Payload too large")

    if not _verify_heygen_signature(body_bytes, x_heygen_signature):
        raise HTTPException(status_code=401, detail="Invalid signature")

    body = json.loads(body_bytes)

    timestamp_str = body.get("timestamp")
    if timestamp_str:
        try:
            webhook_time = datetime.fromisoformat(timestamp_str.replace("Z", "+00:00"))
            age = (datetime.now(UTC) - webhook_time).total_seconds()
            if age > _MAX_WEBHOOK_AGE_SECONDS:
                return {"status": "stale"}
        except (ValueError, TypeError):
            pass

    job_id = body.get("data", {}).get("video_id") or body.get("event_data", {}).get("id")
    event = body.get("event", "unknown")
    video_url = body.get("data", {}).get("video_url") or body.get("event_data", {}).get("video_url")

    if job_id:
        if await _is_duplicate(f"heygen:{job_id}"):
            return {"status": "duplicate"}
        _fire_background_job(job_id, {
            "status": event,
            "video_url": video_url,
            "provider": "heygen",
        })

    return {"status": "ok"}


@router.post("/replicate")
async def replicate_webhook(
    request: Request,
    x_replicate_webhook_secret: str | None = Header(None),
) -> dict[str, str]:
    body_bytes = await request.body()
    if len(body_bytes) > _MAX_BODY_BYTES:
        raise HTTPException(status_code=413, detail="Payload too large")

    if not _verify_replicate_signature(body_bytes, x_replicate_webhook_secret):
        raise HTTPException(status_code=401, detail="Invalid signature")

    body = json.loads(body_bytes)
    prediction_id = body.get("id")
    status = body.get("status", "unknown")
    output = body.get("output")

    if not prediction_id or not isinstance(prediction_id, str) or len(prediction_id) > 64:
        return {"status": "ignored", "reason": "invalid_prediction_id"}

    if not prediction_id.startswith(("pred_", "p_")):
        logger.warning("Unexpected prediction_id format: %s", prediction_id[:16])
        return {"status": "ignored", "reason": "unexpected_id_format"}
    image_url = None
    video_url = None
    if isinstance(output, list):
        image_url = output[0] if output else None
    elif isinstance(output, str):
        image_url = output

    if prediction_id and status == "succeeded":
        if await _is_duplicate(f"replicate:{prediction_id}"):
            return {"status": "duplicate"}
        result = {"status": status, "provider": "replicate"}
        if image_url:
            result["image_url"] = image_url
        if video_url:
            result["video_url"] = video_url
        _fire_background_job(prediction_id, result)

    return {"status": "ok"}
