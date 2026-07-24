from __future__ import annotations

from typing import Any

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from backend.app.db.internship_state import InternshipState
from backend.app.db.training_signal import TrainingSignal
from backend.app.modules.agents.base import BaseAgent


class TrainingAgent(BaseAgent):
    name = "training"
    description = "Обработка сигналов стажировки и обновление модели предпочтений"

    WEIGHTS = {
        "approved": 1.0,
        "approved_with_edits": 1.5,
        "rejected": 1.0,
        "rejected_with_comment": 3.0,
        "deleted_after_publish": 2.0,
        "marked_as_best": 2.5,
    }

    async def execute(
        self,
        session: AsyncSession,
        input_data: dict[str, Any],
        context: dict[str, Any] | None = None,
    ) -> dict[str, Any]:
        project_id = input_data.get("project_id", (context or {}).get("project_id"))
        tenant_id = input_data.get("tenant_id", (context or {}).get("tenant_id"))
        action = input_data.get("action")
        content_item_id = input_data.get("content_item_id")
        comment = input_data.get("comment")
        signal_context = input_data.get("context", {})

        internship = await session.scalar(
            select(InternshipState).where(
                InternshipState.tenant_id == tenant_id,
                InternshipState.project_id == project_id,
            )
        )

        if not internship:
            return {"error": "Internship not started for this project"}

        weight = self.WEIGHTS.get(action, 1.0)

        signal = TrainingSignal(
            tenant_id=tenant_id,
            project_id=project_id,
            content_item_id=content_item_id,
            action=action,
            signal_weight=weight,
            comment=comment,
            context={
                **signal_context,
                "internship_day": internship.day_number,
                "internship_stage": internship.stage,
            },
            training_round=internship.signals_count,
        )
        session.add(signal)
        internship.signals_count += 1

        if action in ("approved", "approved_with_edits", "marked_as_best"):
            internship.approved_count += 1
        internship.generated_count += 1

        approval_rate = internship.approved_count / max(internship.generated_count, 1)
        internship.approval_rate = approval_rate

        prefs = internship.preference_model or {}
        topic = signal_context.get("topic")
        fmt = signal_context.get("format")
        tone = signal_context.get("tone")

        for key, value in [("topics", topic), ("formats", fmt), ("tones", tone)]:
            if value:
                category = prefs.setdefault(key, {})
                current = category.setdefault(value, 0.0)
                if action in ("approved", "approved_with_edits", "marked_as_best"):
                    category[value] = current + weight
                elif action in ("rejected", "rejected_with_comment", "deleted_after_publish"):
                    category[value] = current - weight

        internship.preference_model = prefs

        await session.flush()

        return {
            "signal_id": signal.id,
            "internship_day": internship.day_number,
            "internship_stage": internship.stage,
            "approval_rate": round(approval_rate, 4),
            "total_signals": internship.signals_count,
            "recommended_mode": internship.recommended_mode,
        }
