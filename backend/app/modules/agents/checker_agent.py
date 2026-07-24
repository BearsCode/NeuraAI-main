from __future__ import annotations

from typing import Any

from sqlalchemy.ext.asyncio import AsyncSession

from backend.app.integrations import ai_client
from backend.app.modules.agents.base import BaseAgent
from backend.app.services_internal.business_memory import BusinessMemoryService


class CheckerAgent(BaseAgent):
    name = "checker"
    description = "Орфография, запрещённые темы, соответствие бренду"

    def __init__(self):
        self.memory = BusinessMemoryService()

    async def execute(
        self,
        session: AsyncSession,
        input_data: dict[str, Any],
        context: dict[str, Any] | None = None,
    ) -> dict[str, Any]:
        text = input_data.get("text", "")
        project_id = input_data.get("project_id", (context or {}).get("project_id"))
        tenant_id = input_data.get("tenant_id", (context or {}).get("tenant_id"))
        images = input_data.get("images", [])

        profile = await self.memory.get_company_profile(session, tenant_id, project_id)
        restrictions = profile.get("content_restrictions", "")

        prompt = (
            f"Check this content for issues before publication.\n\n"
            f"CONTENT:\n{text[:3000]}\n\n"
            f"Brand restrictions: {restrictions}\n"
            f"Images count: {len(images)}\n\n"
            f"Check for:\n"
            f"1. Spelling and grammar errors\n"
            f"2. Brand voice compliance\n"
            f"3. Prohibited topics\n"
            f"4. Offensive or inappropriate content\n"
            f"5. Missing required elements (CTA, hashtags)\n\n"
            f"Return JSON with: passed (bool), issues (array of objects with severity, description, suggestion), "
            f"overall_score (int 1-100), summary (str)"
        )

        result = await ai_client.generate(prompt=prompt, response_format={"type": "json_object"})

        check_result = result if isinstance(result, dict) else {"passed": True, "issues": []}

        return {
            "passed": check_result.get("passed", True),
            "issues": check_result.get("issues", []),
            "overall_score": check_result.get("overall_score", 100),
            "summary": check_result.get("summary", "Content checked"),
        }
