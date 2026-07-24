from __future__ import annotations

from typing import Any

from sqlalchemy.ext.asyncio import AsyncSession

from backend.app.integrations import ai_client
from backend.app.modules.agents.base import BaseAgent
from backend.app.services_internal.business_memory import BusinessMemoryService


class MarketingAgent(BaseAgent):
    name = "marketing"
    description = "Контентная стратегия: форматы, частота, рубрики, KPI"

    def __init__(self):
        self.memory = BusinessMemoryService()

    async def execute(
        self,
        session: AsyncSession,
        input_data: dict[str, Any],
        context: dict[str, Any] | None = None,
    ) -> dict[str, Any]:
        project_id = input_data.get("project_id", (context or {}).get("project_id"))
        tenant_id = input_data.get("tenant_id", (context or {}).get("tenant_id"))

        context_data = await self.memory.get_full_context(session, tenant_id, project_id)

        prompt = (
            f"Create a content marketing strategy for this business.\n"
            f"Profile: {context_data.get('company_profile')}\n"
            f"Analytics: {context_data.get('analytics')}\n"
            f"Preferences: {context_data.get('preferences')}\n"
            f"Topics: {context_data.get('topic_model')}\n"
            f"Return JSON with: content_rubrics (list), posting_frequency (str), "
            f"best_formats (list), kpi_suggestions (list), content_mix (dict)"
        )

        result = await ai_client.generate(prompt=prompt, response_format={"type": "json_object"})
        return result if isinstance(result, dict) else {"strategy": str(result)}
