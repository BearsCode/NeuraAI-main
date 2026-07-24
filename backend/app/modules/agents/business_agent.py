from __future__ import annotations

from typing import Any

from sqlalchemy.ext.asyncio import AsyncSession

from backend.app.integrations import ai_client
from backend.app.modules.agents.base import BaseAgent
from backend.app.services_internal.business_memory import BusinessMemoryService


class BusinessAgent(BaseAgent):
    name = "business"
    description = "Анализ компании, SWOT, позиционирование, конкуренты"

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
        if not project_id or not tenant_id:
            return {"error": "project_id and tenant_id required"}

        profile = await self.memory.get_company_profile(session, tenant_id, project_id)

        prompt = (
            f"Analyze this business and perform a SWOT analysis.\n"
            f"Company: {profile.get('company_name')}\n"
            f"Description: {profile.get('company_description')}\n"
            f"Niche: {profile.get('company_niche')}\n"
            f"Target audience: {profile.get('target_audience')}\n"
            f"Brand voice: {profile.get('brand_voice')}\n"
            f"Return JSON with: swot (strengths, weaknesses, opportunities, threats), "
            f"positioning (str), competitors (list), recommendations (list)"
        )

        result = await ai_client.generate(prompt=prompt, response_format={"type": "json_object"})
        return result if isinstance(result, dict) else {"analysis": str(result)}
