from __future__ import annotations

import asyncio
import json
import os
from datetime import UTC, datetime
from typing import Any

from redis.asyncio import Redis
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from backend.app.core.redis import get_redis_client
from backend.app.db.ai_job import AIJob
from backend.app.db.enums import WorkflowStatus
from backend.app.db.workflow_instance import WorkflowInstance
from backend.app.db.workflow_step import WorkflowStep


_LOCK_RELEASE_SCRIPT = """
if redis.call("get", KEYS[1]) == ARGV[1] then
    return redis.call("del", KEYS[1])
else
    return 0
end
"""

_CONTEXT_UPDATE_SCRIPT = """
local key = KEYS[1]
local ttl = ARGV[#ARGV]
local updates = cjson.decode(ARGV[#ARGV - 1])
local existing = redis.call("get", key)
if not existing then
    return nil
end
local ctx = cjson.decode(existing)
for k, v in pairs(updates) do
    ctx[k] = v
end
redis.call("set", key, cjson.encode(ctx))
if tonumber(ttl) > 0 then
    redis.call("expire", key, tonumber(ttl))
end
return cjson.encode(ctx)
"""


class StateManager:
    def __init__(self, redis: Redis | None = None):
        self.redis = redis or get_redis_client()
        self._instance_id = os.urandom(8).hex()

    LOCK_TTL = 300
    STATE_TTL = 86400
    CHECKPOINT_PREFIX = "wf:chkpt:"
    LOCK_PREFIX = "wf:lock:"
    CONTEXT_PREFIX = "wf:ctx:"
    ASYNC_PREFIX = "wf:async:"

    async def acquire_lock(
        self, workflow_id: str, ttl: int | None = None, retry: bool = True
    ) -> bool:
        key = f"{self.LOCK_PREFIX}{workflow_id}"
        max_attempts = 4 if retry else 1
        for attempt in range(max_attempts):
            acquired = await self.redis.set(
                key, self._instance_id, nx=True, ex=ttl or self.LOCK_TTL
            )
            if acquired:
                return True
            if attempt < max_attempts - 1:
                await asyncio.sleep(0.05 * (2 ** attempt))
        return False

    async def release_lock(self, workflow_id: str) -> None:
        key = f"{self.LOCK_PREFIX}{workflow_id}"
        await self.redis.eval(_LOCK_RELEASE_SCRIPT, 1, key, self._instance_id)

    async def extend_lock(self, workflow_id: str, ttl: int | None = None) -> bool:
        key = f"{self.LOCK_PREFIX}{workflow_id}"
        val = await self.redis.get(key)
        if val and val.decode() == self._instance_id:
            return bool(await self.redis.expire(key, ttl or self.LOCK_TTL))
        return False

    async def save_context(
        self, workflow_id: str, context: dict[str, Any], ttl: int | None = None
    ) -> None:
        key = f"{self.CONTEXT_PREFIX}{workflow_id}"
        await self.redis.set(
            key, json.dumps(context, default=str),
            ex=ttl or self.STATE_TTL,
        )

    async def get_context(self, workflow_id: str) -> dict[str, Any] | None:
        key = f"{self.CONTEXT_PREFIX}{workflow_id}"
        data = await self.redis.get(key)
        if data is None:
            return None
        return json.loads(data)

    async def clear_context(self, workflow_id: str) -> None:
        key = f"{self.CONTEXT_PREFIX}{workflow_id}"
        await self.redis.delete(key)

    async def update_context(
        self, workflow_id: str, updates: dict[str, Any]
    ) -> dict[str, Any] | None:
        key = f"{self.CONTEXT_PREFIX}{workflow_id}"
        ttl = self.STATE_TTL
        result = await self.redis.eval(
            _CONTEXT_UPDATE_SCRIPT, 1, key,
            json.dumps(updates, default=str), str(ttl),
        )
        if result is None:
            return None
        return json.loads(result)

    async def checkpoint(
        self, session: AsyncSession, workflow_id: str
    ) -> None:
        workflow = await session.get(WorkflowInstance, workflow_id)
        if not workflow:
            raise ValueError(f"Workflow {workflow_id} not found")

        key = f"{self.CHECKPOINT_PREFIX}{workflow_id}"
        checkpoint = {
            "status": workflow.status,
            "current_step": workflow.current_step,
            "context": workflow.context,
            "error": workflow.error,
            "result": workflow.result,
            "updated_at": datetime.now(UTC).isoformat(),
        }
        await self.redis.set(
            key, json.dumps(checkpoint, default=str),
            ex=self.STATE_TTL,
        )

    async def get_checkpoint(
        self, workflow_id: str
    ) -> dict[str, Any] | None:
        key = f"{self.CHECKPOINT_PREFIX}{workflow_id}"
        data = await self.redis.get(key)
        if data is None:
            return None
        return json.loads(data)

    async def clear_checkpoint(self, workflow_id: str) -> None:
        key = f"{self.CHECKPOINT_PREFIX}{workflow_id}"
        await self.redis.delete(key)

    async def restore_from_checkpoint(
        self, session: AsyncSession, workflow_id: str
    ) -> WorkflowInstance | None:
        checkpoint = await self.get_checkpoint(workflow_id)
        if checkpoint is None:
            return None

        workflow = await session.get(WorkflowInstance, workflow_id)
        if not workflow:
            return None

        workflow.context = checkpoint.get("context", workflow.context)
        workflow.current_step = checkpoint.get("current_step", workflow.current_step)
        workflow.status = checkpoint.get("status", workflow.status)
        workflow.error = checkpoint.get("error", workflow.error)
        workflow.result = checkpoint.get("result", workflow.result)
        await session.flush()
        return workflow

    async def track_async_job(
        self, step_id: str, job_id: str, ttl: int | None = None
    ) -> None:
        key = f"{self.ASYNC_PREFIX}{step_id}"
        await self.redis.set(
            key, job_id, ex=ttl or self.STATE_TTL,
        )

    async def get_async_job_for_step(self, step_id: str) -> str | None:
        key = f"{self.ASYNC_PREFIX}{step_id}"
        val = await self.redis.get(key)
        return val

    async def remove_async_job(self, step_id: str) -> None:
        key = f"{self.ASYNC_PREFIX}{step_id}"
        await self.redis.delete(key)

    async def pause_workflow(
        self, session: AsyncSession, workflow_id: str
    ) -> WorkflowInstance:
        workflow = await session.get(WorkflowInstance, workflow_id)
        if not workflow:
            raise ValueError(f"Workflow {workflow_id} not found")
        workflow.status = WorkflowStatus.WAITING_ASYNC.value
        await session.flush()
        await self.checkpoint(session, workflow_id)
        return workflow

    async def resume_workflow(
        self, session: AsyncSession, workflow_id: str
    ) -> WorkflowInstance:
        workflow = await session.get(WorkflowInstance, workflow_id)
        if not workflow:
            raise ValueError(f"Workflow {workflow_id} not found")
        workflow.status = WorkflowStatus.RUNNING.value
        await session.flush()
        await self.checkpoint(session, workflow_id)
        return workflow

    async def cancel_workflow(
        self, session: AsyncSession, workflow_id: str
    ) -> WorkflowInstance:
        workflow = await session.get(WorkflowInstance, workflow_id)
        if not workflow:
            raise ValueError(f"Workflow {workflow_id} not found")
        workflow.status = WorkflowStatus.CANCELED.value
        workflow.completed_at = datetime.now(UTC)
        await session.flush()

        steps = (
            await session.scalars(
                select(WorkflowStep).where(
                    WorkflowStep.workflow_id == workflow_id,
                    WorkflowStep.status.in_(["pending", "running"]),
                )
            )
        ).all()
        for step in steps:
            step.status = "canceled"
            step.error = "Workflow was cancelled"
            if step.async_job_id:
                await self.remove_async_job(step.id)

        await self.clear_context(workflow_id)
        await self.clear_checkpoint(workflow_id)
        return workflow

    async def link_job_to_step(
        self, session: AsyncSession, step_id: str, job_id: str
    ) -> None:
        step = await session.get(WorkflowStep, step_id)
        if not step:
            raise ValueError(f"WorkflowStep {step_id} not found")
        step.async_job_id = job_id
        await session.flush()
        await self.track_async_job(step_id, job_id)

    async def get_step_by_job(
        self, session: AsyncSession, job_id: str
    ) -> WorkflowStep | None:
        step = await session.scalar(
            select(WorkflowStep).where(WorkflowStep.async_job_id == job_id)
        )
        return step

    async def resolve_job_step(
        self, session: AsyncSession, step_id: str
    ) -> tuple[WorkflowStep | None, AIJob | None]:
        step = await session.get(WorkflowStep, step_id)
        if not step or not step.async_job_id:
            return step, None
        job = await session.get(AIJob, step.async_job_id)
        return step, job

    async def update_step_result(
        self,
        session: AsyncSession,
        step_id: str,
        result: dict[str, Any],
        status: str | None = None,
    ) -> WorkflowStep | None:
        step = await session.get(WorkflowStep, step_id)
        if not step:
            return None
        if step.status == "completed":
            return step
        step.output_data = result
        step.completed_at = datetime.now(UTC)
        if status:
            step.status = status
        else:
            step.status = "completed"

        workflow = await session.get(WorkflowInstance, step.workflow_id)
        if workflow and workflow.status == WorkflowStatus.WAITING_ASYNC.value:
            workflow.status = WorkflowStatus.RUNNING.value
            await session.flush()
            await self.checkpoint(session, workflow.id)

        await session.commit()
        return step

    async def step_has_active_job(self, step: WorkflowStep) -> bool:
        if not step.async_job_id:
            return False
        job_key = f"{self.ASYNC_PREFIX}{step.id}"
        cached = await self.redis.get(job_key)
        if cached is None:
            return False
        return cached == step.async_job_id
