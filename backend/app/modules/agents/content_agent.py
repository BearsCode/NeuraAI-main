from __future__ import annotations

from typing import Any

from sqlalchemy.ext.asyncio import AsyncSession

from backend.app.db.content_item import ContentItem
from backend.app.db.enums import ContentStatus
from backend.app.integrations import ai_client
from backend.app.modules.agents.base import BaseAgent
from backend.app.services_internal.business_memory import BusinessMemoryService


class ContentAgent(BaseAgent):
    name = "content"
    description = "Генерация и адаптация текстов, хэштеги, подбор под платформу"

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
        platform = input_data.get("platform", "telegram")
        product_data = input_data.get("product_data")

        profile = await self.memory.get_company_profile(session, tenant_id, project_id)
        preferences = await self.memory.get_preference_model(session, tenant_id, project_id)

        prompt = (
            f"Write a social media post for this business.\n"
            f"Company: {profile.get('company_name')}\n"
            f"Niche: {profile.get('company_niche')}\n"
            f"Voice: {profile.get('brand_voice')}\n"
            f"Topic: {topic}\n"
            f"Platform: {platform}\n"
            f"Format: {input_data.get('format', 'post')}\n"
            f"Product data: {product_data}\n"
            f"Preferred tone: {preferences.get('tone_preference', {})}\n"
            f"Return JSON with: text (str), hashtags (list of str), "
            f"call_to_action (str), tone (str), reading_time_seconds (int)"
        )

        result = await ai_client.generate(prompt=prompt, response_format={"type": "json_object"})
        text = (result if isinstance(result, dict) else {}).get("text", str(result))

        from backend.app.db.enums import ContentType as ContentTypeEnum

        content_item = ContentItem(
            tenant_id=tenant_id,
            project_id=project_id,
            content_type=ContentTypeEnum.POST,
            status=ContentStatus.GENERATED,
            text=text,
            metadata_json={
                "topic": topic,
                "platform": platform,
                "hashtags": (result if isinstance(result, dict) else {}).get("hashtags", []),
                "call_to_action": (result if isinstance(result, dict) else {}).get("call_to_action"),
                "tone": (result if isinstance(result, dict) else {}).get("tone"),
                "full_response": result if isinstance(result, dict) else {},
            },
        )
        session.add(content_item)
        await session.flush()

        return {
            "content_item_id": content_item.id,
            "text": text,
            "metadata": result if isinstance(result, dict) else {"text": str(result)},
        }
