from __future__ import annotations

from uuid import uuid4

from redis.asyncio import Redis

from backend.app.core.configs import settings


class QueueClient:
    def __init__(self) -> None:
        self._redis: Redis | None = None

    async def connect(self) -> None:
        if settings.queue_backend != "redis" or self._redis is not None:
            return

        self._redis = Redis.from_url(
            settings.redis_url,
            encoding="utf-8",
            decode_responses=True,
        )
        await self._redis.ping()

    async def close(self) -> None:
        if self._redis is not None:
            await self._redis.aclose()
            self._redis = None

    async def enqueue_publication(self, publication_id: str) -> str:
        job_id = f"publication:{uuid4().hex}"

        if settings.queue_backend == "redis":
            await self.connect()
            assert self._redis is not None
            await self._redis.xadd(
                "publication_queue",
                {
                    "job_id": job_id,
                    "publication_id": publication_id,
                },
            )
            return job_id

        return f"{settings.queue_backend}:{publication_id}:{uuid4().hex[:8]}"

    async def healthcheck(self) -> dict[str, str]:
        if settings.queue_backend != "redis":
            return {
                "status": "ok",
                "backend": settings.queue_backend,
            }

        try:
            await self.connect()
            return {
                "status": "ok",
                "backend": "redis",
            }
        except Exception as exc:
            return {
                "status": "down",
                "backend": "redis",
                "detail": str(exc),
            }
