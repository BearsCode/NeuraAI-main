from __future__ import annotations

from datetime import UTC, datetime

from sqlalchemy import desc, select
from sqlalchemy.ext.asyncio import AsyncSession

from backend.app.db.enums import InternshipStage
from backend.app.db.internship_state import InternshipState
from backend.app.db.training_signal import TrainingSignal
from backend.app.modules.agents.training_agent import TrainingAgent


class InternshipService:
    def __init__(self):
        self.training_agent = TrainingAgent()

    async def start_internship(
        self, session: AsyncSession, tenant_id: str, project_id: str
    ) -> dict:
        existing = await session.scalar(
            select(InternshipState).where(
                InternshipState.tenant_id == tenant_id,
                InternshipState.project_id == project_id,
            )
        )
        if existing:
            return {
                "status": "already_exists",
                "stage": existing.stage,
                "day": existing.day_number,
            }

        state = InternshipState(
            tenant_id=tenant_id,
            project_id=project_id,
            stage=InternshipStage.INITIALIZATION.value,
            day_number=1,
            total_days=14,
            started_at=datetime.now(UTC),
        )
        session.add(state)
        await session.commit()

        return {
            "status": "started",
            "stage": "initialization",
            "day": 1,
            "total_days": 14,
            "project_id": project_id,
        }

    async def get_status(
        self, session: AsyncSession, tenant_id: str, project_id: str
    ) -> dict:
        state = await session.scalar(
            select(InternshipState).where(
                InternshipState.tenant_id == tenant_id,
                InternshipState.project_id == project_id,
            )
        )
        if not state:
            return {"status": "not_started"}

        signals = (
            await session.scalars(
                select(TrainingSignal)
                .where(
                    TrainingSignal.tenant_id == tenant_id,
                    TrainingSignal.project_id == project_id,
                )
                .order_by(desc(TrainingSignal.created_at))
                .limit(10)
            )
        ).all()

        return {
            "status": "in_progress",
            "stage": state.stage,
            "day": state.day_number,
            "total_days": state.total_days,
            "approval_rate": state.approval_rate,
            "signals_count": state.signals_count,
            "generated_count": state.generated_count,
            "approved_count": state.approved_count,
            "is_extended": state.is_extended,
            "recommended_mode": state.recommended_mode,
            "preference_model_summary": {
                k: dict(sorted(v.items(), key=lambda x: x[1], reverse=True)[:5])
                for k, v in (state.preference_model or {}).items()
            },
            "recent_signals": [
                {
                    "action": s.action,
                    "weight": s.signal_weight,
                    "comment": s.comment,
                    "created_at": s.created_at.isoformat(),
                }
                for s in signals
            ],
        }

    async def evaluate_post(
        self,
        session: AsyncSession,
        tenant_id: str,
        project_id: str,
        payload,
    ) -> dict:
        result = await self.training_agent.execute(
            session,
            {
                "tenant_id": tenant_id,
                "project_id": project_id,
                "action": payload.action,
                "content_item_id": payload.content_item_id,
                "comment": payload.comment,
                "context": payload.context,
            },
        )
        await session.commit()
        return result

    async def set_mode(
        self, session: AsyncSession, tenant_id: str, project_id: str, mode: str
    ) -> dict:
        state = await session.scalar(
            select(InternshipState).where(
                InternshipState.tenant_id == tenant_id,
                InternshipState.project_id == project_id,
            )
        )
        if not state:
            return {"error": "Internship not started"}

        state.recommended_mode = mode
        if mode in ("automatic", "semi_automatic", "manual"):
            state.stage = InternshipStage.COMPLETED.value
            state.completed_at = datetime.now(UTC)

        await session.commit()
        return {"status": "mode_set", "mode": mode}

    async def get_report(
        self, session: AsyncSession, tenant_id: str, project_id: str
    ) -> dict:
        state = await session.scalar(
            select(InternshipState).where(
                InternshipState.tenant_id == tenant_id,
                InternshipState.project_id == project_id,
            )
        )
        if not state:
            return {"error": "Internship not started"}

        top_topics = sorted(
            (state.preference_model or {}).get("topics", {}).items(),
            key=lambda x: x[1],
            reverse=True,
        )[:5]
        top_formats = sorted(
            (state.preference_model or {}).get("formats", {}).items(),
            key=lambda x: x[1],
            reverse=True,
        )[:5]

        return {
            "project_id": project_id,
            "duration_days": state.day_number,
            "total_signals": state.signals_count,
            "approval_rate": state.approval_rate,
            "recommended_mode": state.recommended_mode or "manual",
            "preference_model": state.preference_model,
            "top_topics": top_topics,
            "top_formats": top_formats,
            "is_extended": state.is_extended,
            "completed": state.stage == "completed",
        }

    async def advance_day(
        self, session: AsyncSession, tenant_id: str, project_id: str
    ) -> dict:
        state = await session.scalar(
            select(InternshipState).where(
                InternshipState.tenant_id == tenant_id,
                InternshipState.project_id == project_id,
            )
        )
        if not state:
            return {"error": "Internship not started"}
        if state.stage == "completed":
            return {"status": "already_completed"}

        state.day_number += 1

        if state.stage == InternshipStage.INITIALIZATION.value and state.day_number > 2:
            state.stage = InternshipStage.ACTIVE_LEARNING.value
        elif state.stage == InternshipStage.ACTIVE_LEARNING.value and state.day_number > 7:
            if state.approval_rate and state.approval_rate >= 0.7:
                state.stage = InternshipStage.CALIBRATION.value
            else:
                state.stage = InternshipStage.EXTENDED.value
                state.is_extended = True
                state.total_days += 7
        elif state.stage == InternshipStage.CALIBRATION.value and state.day_number > 12:
            state.stage = InternshipStage.FINAL_CHECK.value
        elif state.stage == InternshipStage.FINAL_CHECK.value and state.day_number >= 14:
            state.stage = InternshipStage.COMPLETED.value
            state.completed_at = datetime.now(UTC)
            if state.approval_rate and state.approval_rate >= 0.85:
                state.recommended_mode = "automatic"
            elif state.approval_rate and state.approval_rate >= 0.6:
                state.recommended_mode = "semi_automatic"
            else:
                state.recommended_mode = "manual"

        await session.commit()

        return {
            "status": "advanced",
            "stage": state.stage,
            "day": state.day_number,
            "total_days": state.total_days,
            "approval_rate": state.approval_rate,
            "recommended_mode": state.recommended_mode,
        }
