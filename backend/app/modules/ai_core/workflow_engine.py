from __future__ import annotations

import asyncio
from datetime import UTC, datetime, timedelta

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from backend.app.db.enums import WorkflowStatus, WorkflowStepType
from backend.app.integrations import ai_client
from backend.app.db.workflow_instance import WorkflowInstance
from backend.app.db.workflow_step import WorkflowStep
from backend.app.events.bus import event_bus
from backend.app.events.schemas import EventEnvelope
from backend.app.modules.agents.base import AgentRegistry
from backend.app.modules.ai_core.circuit_breaker import CircuitBreaker
from backend.app.modules.ai_core.state_manager import StateManager


AI_TIMEOUT = 120
_ai_breaker = CircuitBreaker(name="ai_client", failure_threshold=3, recovery_timeout=30)


class WorkflowEngine:
    def __init__(self):
        self.agent_registry = AgentRegistry()
        self.state_manager = StateManager()

    async def create_workflow(
        self,
        session: AsyncSession,
        tenant_id: str,
        project_id: str,
        workflow_type: str,
        steps: list[dict],
        context: dict | None = None,
        trigger: str | None = None,
        parent_workflow_id: str | None = None,
        do_commit: bool = True,
    ) -> WorkflowInstance:
        workflow = WorkflowInstance(
            tenant_id=tenant_id,
            project_id=project_id,
            workflow_type=workflow_type,
            status=WorkflowStatus.PENDING.value,
            trigger=trigger,
            total_steps=len(steps),
            context=context or {},
            parent_workflow_id=parent_workflow_id,
        )
        session.add(workflow)
        await session.flush()

        for i, step in enumerate(steps):
            step_type = step.get("step_type", WorkflowStepType.GENERATE_TEXT.value)
            agent_type = step.get("agent_type")
            input_data = step.get("input_data", {})
            await self._create_step(session, workflow.id, i, step_type, agent_type, input_data)

        if do_commit:
            await session.commit()
        return workflow

    async def _create_step(
        self,
        session: AsyncSession,
        workflow_id: str,
        order: int,
        step_type: str,
        agent_type: str | None,
        input_data: dict,
    ) -> WorkflowStep:
        step = WorkflowStep(
            workflow_id=workflow_id,
            step_order=order,
            step_type=step_type,
            agent_type=agent_type,
            status="pending",
            input_data=input_data,
        )
        session.add(step)
        await session.flush()
        return step

    async def start_workflow(
        self, session: AsyncSession, workflow_id: str
    ) -> WorkflowInstance:
        workflow = await session.scalar(
            select(WorkflowInstance).where(WorkflowInstance.id == workflow_id)
        )
        if not workflow:
            raise ValueError(f"Workflow {workflow_id} not found")

        if workflow.status in (WorkflowStatus.RUNNING.value, WorkflowStatus.WAITING_ASYNC.value):
            raise ValueError(f"Workflow {workflow_id} is already {workflow.status}")

        if not await self.state_manager.acquire_lock(workflow_id):
            raise ValueError(f"Workflow {workflow_id} is locked by another process")

        try:
            workflow.status = WorkflowStatus.RUNNING.value
            workflow.started_at = datetime.now(UTC)
            await session.flush()
            await session.commit()

            await self._execute_next_step(session, workflow)
        finally:
            await self.state_manager.release_lock(workflow_id)

        return workflow

    async def _execute_next_step(
        self, session: AsyncSession, workflow: WorkflowInstance
    ) -> None:
        steps = (
            await session.scalars(
                select(WorkflowStep)
                .where(
                    WorkflowStep.workflow_id == workflow.id,
                    WorkflowStep.status == "pending",
                )
                .order_by(WorkflowStep.step_order)
                .limit(1)
            )
        ).first() or (
            await session.scalars(
                select(WorkflowStep)
                .where(
                    WorkflowStep.workflow_id == workflow.id,
                    WorkflowStep.status == "failed",
                )
                .order_by(WorkflowStep.step_order)
                .limit(1)
            )
        ).first()

        if not steps:
            workflow.status = WorkflowStatus.COMPLETED.value
            workflow.completed_at = datetime.now(UTC)
            await session.flush()
            await session.commit()

            if event_bus:
                await event_bus.publish(
                    EventEnvelope(
                        event_type="workflow.completed",
                        topic="workflow.completed.v1",
                        tenant_id=workflow.tenant_id,
                        aggregate_id=workflow.id,
                        payload={
                            "workflow_id": workflow.id,
                            "workflow_type": workflow.workflow_type,
                            "project_id": workflow.project_id,
                            "result": workflow.result,
                        },
                    )
                )
            return

        step = steps
        step.status = "running"
        step.started_at = datetime.now(UTC)
        await session.flush()
        await self.state_manager.checkpoint(session, workflow.id)

        try:
            agent = self.agent_registry.get_agent(step.agent_type) if step.agent_type else None
            if agent:
                result = await agent.execute(session, step.input_data, workflow.context)
                step.output_data = result if isinstance(result, dict) else {"result": str(result)}
            else:
                step.output_data = await self._execute_step_type(session, step, workflow)

            step.status = "completed"
            step.completed_at = datetime.now(UTC)
            workflow.current_step = step.step_order + 1
            workflow.context.update({"last_step_output": step.output_data})
            await session.flush()
            await session.commit()

            await self.state_manager.extend_lock(workflow.id)

            await self._execute_next_step(session, workflow)
        except Exception as e:
            step.status = "failed"
            step.error = str(e)
            step.retry_count += 1
            await session.flush()
            await self.state_manager.checkpoint(session, workflow.id)

            if step.retry_count < workflow.max_retries:
                step.status = "pending"
                step.error = None
                await session.flush()
                await session.commit()
                await self._execute_next_step(session, workflow)
            else:
                workflow.status = WorkflowStatus.FAILED.value
                workflow.error = f"Step {step.step_order} failed after {step.retry_count} retries: {e}"
                workflow.completed_at = datetime.now(UTC)
                await session.commit()

                if event_bus:
                    await event_bus.publish(
                        EventEnvelope(
                            event_type="workflow.failed",
                            topic="workflow.failed.v1",
                            tenant_id=workflow.tenant_id,
                            aggregate_id=workflow.id,
                            payload={
                                "workflow_id": workflow.id,
                                "workflow_type": workflow.workflow_type,
                                "project_id": workflow.project_id,
                                "error": str(e),
                                "step": step.step_order,
                            },
                        )
                    )

    async def _execute_step_type(
        self, session: AsyncSession, step: WorkflowStep, workflow: WorkflowInstance
    ) -> dict:
        step_type = step.step_type
        input_data = step.input_data

        if step_type == WorkflowStepType.GENERATE_TEXT.value:
            prompt = input_data.get("prompt", "")
            topic = input_data.get("topic", "general")
            platform = input_data.get("platform", "telegram")
            if prompt:
                result = await asyncio.wait_for(
                    _ai_breaker.call(
                        ai_client.generate,
                        prompt=prompt,
                        response_format={"type": "json_object"} if input_data.get("response_format") == "json" else None,
                    ),
                    timeout=AI_TIMEOUT,
                )
                return {"generated_text": result, "topic": topic, "platform": platform}
            return input_data

        elif step_type == WorkflowStepType.GENERATE_IMAGE.value:
            prompt = input_data.get("prompt", "")
            if prompt:
                url = await asyncio.wait_for(
                    _ai_breaker.call(ai_client.generate_image, prompt),
                    timeout=AI_TIMEOUT,
                )
                return {"image_url": url, "prompt": prompt}
            return {"image_url": None}

        elif step_type == WorkflowStepType.CHECK_CONTENT.value:
            content = input_data.get("content") or workflow.context.get("last_step_output", {}).get("generated_text", "")
            if content:
                check_prompt = (
                    f"Review this social media content for compliance, quality, and brand safety:\n\n{content}\n\n"
                    f"Return JSON with: approved (bool), issues (list of strings), score (int 0-100)"
                )
                result = await asyncio.wait_for(
                    _ai_breaker.call(
                        ai_client.generate,
                        prompt=check_prompt,
                        response_format={"type": "json_object"},
                    ),
                    timeout=AI_TIMEOUT,
                )
                return result if isinstance(result, dict) else {"approved": True, "issues": [], "score": 85}
            return {"approved": True, "issues": [], "score": 100}

        elif step_type == WorkflowStepType.PUBLISH.value:
            publication_id = input_data.get("publication_id")
            if publication_id:
                from backend.app.modules.ai_core.publisher_service import PublisherService
                publisher = PublisherService()
                try:
                    return await publisher.publish(session, publication_id)
                except ValueError as e:
                    return {"status": "failed", "error": str(e)}
            return {"status": "skipped", "reason": "No publication_id provided"}

        elif step_type == WorkflowStepType.NOTIFY.value:
            return {"notified": True}

        elif step_type == WorkflowStepType.SPLIT.value:
            branches = input_data.get("branches", [])
            child_ids = []
            for branch in branches:
                child = await self.create_child_workflow(
                    session, workflow.id,
                    workflow_type=workflow.workflow_type,
                    steps=branch.get("steps", []),
                    context={**workflow.context, **(branch.get("context", {}))},
                )
                child_ids.append(child.id)
            return {"child_workflow_ids": child_ids, "branch_count": len(child_ids)}

        elif step_type == WorkflowStepType.MERGE.value:
            child_ids = input_data.get("child_workflow_ids", [])
            merged = {"child_results": []}
            for cid in child_ids:
                child = await self.get_workflow(session, cid)
                if child:
                    merged["child_results"].append(child.get("result", {}))
            return merged

        elif step_type == WorkflowStepType.WAIT_ASYNC.value:
            job_id = input_data.get("async_job_id")
            if job_id:
                timeout_minutes = float(input_data.get("timeout_minutes", 60))
                workflow.context["wait_deadline"] = (
                    datetime.now(UTC) + timedelta(minutes=timeout_minutes)
                ).isoformat()
                await self.state_manager.pause_workflow(session, workflow.id)
            return {"waiting_for": job_id, "status": "async_pending"}

        else:
            return {"processed": True, "data": input_data}

    async def get_workflow(
        self, session: AsyncSession, workflow_id: str
    ) -> dict | None:
        workflow = await session.scalar(
            select(WorkflowInstance).where(WorkflowInstance.id == workflow_id)
        )
        if not workflow:
            return None

        steps = (
            await session.scalars(
                select(WorkflowStep)
                .where(WorkflowStep.workflow_id == workflow_id)
                .order_by(WorkflowStep.step_order)
                .limit(500)
            )
        ).all()

        return {
            "id": workflow.id,
            "tenant_id": workflow.tenant_id,
            "project_id": workflow.project_id,
            "workflow_type": workflow.workflow_type,
            "status": workflow.status,
            "trigger": workflow.trigger,
            "current_step": workflow.current_step,
            "total_steps": workflow.total_steps,
            "context": workflow.context,
            "result": workflow.result,
            "error": workflow.error,
            "started_at": workflow.started_at.isoformat() if workflow.started_at else None,
            "completed_at": workflow.completed_at.isoformat() if workflow.completed_at else None,
            "steps": [
                {
                    "id": s.id,
                    "step_order": s.step_order,
                    "step_type": s.step_type,
                    "agent_type": s.agent_type,
                    "status": s.status,
                    "input_data": s.input_data,
                    "output_data": s.output_data,
                    "error": s.error,
                }
                for s in steps
            ],
        }

    async def create_child_workflow(
        self,
        session: AsyncSession,
        parent_workflow_id: str,
        workflow_type: str,
        steps: list[dict],
        context: dict | None = None,
    ) -> WorkflowInstance:
        parent = await session.scalar(
            select(WorkflowInstance).where(WorkflowInstance.id == parent_workflow_id)
        )
        if not parent:
            raise ValueError(f"Parent workflow {parent_workflow_id} not found")

        return await self.create_workflow(
            session=session,
            tenant_id=parent.tenant_id,
            project_id=parent.project_id,
            workflow_type=workflow_type,
            steps=steps,
            context=context or parent.context.copy(),
            trigger=f"child_of_{parent_workflow_id}",
            parent_workflow_id=parent_workflow_id,
            do_commit=False,
        )
