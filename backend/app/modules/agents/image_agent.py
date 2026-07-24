from __future__ import annotations

from typing import Any

from sqlalchemy.ext.asyncio import AsyncSession

from backend.app.integrations import ai_client, storage_client
from backend.app.modules.agents.base import BaseAgent
from backend.app.services_internal.business_memory import BusinessMemoryService


class ImageAgent(BaseAgent):
    name = "image"
    description = "Генерация изображений (DALL-E + фото-аватар)"

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
        use_avatar = input_data.get("use_avatar", False)
        product_data = input_data.get("product_data")

        profile = await self.memory.get_company_profile(session, tenant_id, project_id)

        prompt = (
            f"Generate an image prompt for a social media post.\n"
            f"Company: {profile.get('company_name')}\n"
            f"Niche: {profile.get('company_niche')}\n"
            f"Topic: {topic}\n"
            f"Use owner avatar: {use_avatar}\n"
            f"Product: {product_data}\n"
            f"Return JSON with: image_prompt (str, detailed English prompt for DALL-E), "
            f"style (str), mood (str)"
        )

        image_prompt_result = await ai_client.generate(prompt=prompt, response_format={"type": "json_object"})
        image_prompt = (image_prompt_result if isinstance(image_prompt_result, dict) else {}).get(
            "image_prompt", topic
        )

        image_url = await ai_client.generate_image(prompt=image_prompt)

        stored_url = await storage_client.upload_from_url(image_url, f"{tenant_id}/{project_id}/images/")

        return {
            "image_url": stored_url,
            "original_prompt": image_prompt,
            "metadata": image_prompt_result if isinstance(image_prompt_result, dict) else {},
        }
