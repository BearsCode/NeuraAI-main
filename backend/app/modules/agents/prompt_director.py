from __future__ import annotations

import json
from typing import Any

from sqlalchemy.ext.asyncio import AsyncSession

from backend.app.integrations import ai_client
from backend.app.modules.agents.base import BaseAgent
from backend.app.services_internal.business_memory import BusinessMemoryService


class PromptDirectorAgent(BaseAgent):
    name = "prompt_director"
    description = "Переводит тему в точное техническое задание для видео-агентов (Видео-бриф)"

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
        
        topic = input_data.get("topic", "general")
        platform = input_data.get("platform", "instagram")
        format_type = input_data.get("format", "Reels")
        product_data = input_data.get("product_data", {})
        brand_data = input_data.get("brand_data", {})

        profile = await self.memory.get_company_profile(session, tenant_id, project_id)

        prompt = (
            f"You are a Prompt Director. Translate the given topic into a precise Video Brief for Editor Agent.\n"
            f"Business Profile:\n"
            f"Company: {profile.get('company_name')}\n"
            f"Niche: {profile.get('company_niche')}\n"
            f"Voice: {profile.get('brand_voice')}\n\n"
            f"Input Data:\n"
            f"Topic: {topic}\n"
            f"Platform: {platform}\n"
            f"Format: {format_type}\n"
            f"Product Catalog Data: {json.dumps(product_data, ensure_ascii=False)}\n"
            f"Brand Data: {json.dumps(brand_data, ensure_ascii=False)}\n\n"
            f"Follow the 5-point formula:\n"
            f"1. Duration (in seconds, based on format)\n"
            f"2. Platform & Aspect Ratio (e.g. 9:16 for Reels/Stories, 1:1 or 16:9 for others)\n"
            f"3. Scene structure (timing, description, source - catalog, generated, or stock_background)\n"
            f"4. Visual style (colors, fonts, mood)\n"
            f"5. Branding (logo position, appearance timing)\n\n"
            f"Return JSON strictly with the following structure:\n"
            f"{{\n"
            f"  \"duration_sec\": number,\n"
            f"  \"platform\": string,\n"
            f"  \"aspect_ratio\": string,\n"
            f"  \"scenes\": [\n"
            f"    {{ \"timing\": string, \"description\": string, \"source\": \"catalog|generated|stock_background\", "
            f"\"catalog_item_id\": string|null, \"generation_agent\": string|null, \"stock_search_query\": string|null }}\n"
            f"  ],\n"
            f"  \"visual_style\": {{ \"colors\": [string], \"fonts\": [string], \"mood\": string }},\n"
            f"  \"branding\": {{ \"logo_position\": string, \"appears_at_sec\": number }}\n"
            f"}}"
        )

        result = await ai_client.generate(prompt=prompt, response_format={"type": "json_object"})
        
        # Ensure result is a dictionary
        brief_data = result if isinstance(result, dict) else json.loads(str(result))

        return {
            "brief": brief_data,
            "topic": topic,
            "platform": platform,
            "format": format_type
        }
