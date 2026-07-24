from __future__ import annotations

from typing import Any

from sqlalchemy.ext.asyncio import AsyncSession

from backend.app.integrations import ai_client, storage_client
from backend.app.modules.agents.base import BaseAgent
from backend.app.services_internal.business_memory import BusinessMemoryService


class VideoAgent(BaseAgent):
    name = "video"
    description = "Скрипт → HeyGen видео-аватар → субтитры → финальный файл"

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
        duration_seconds = input_data.get("duration_seconds", 30)
        avatar_id = input_data.get("avatar_id")

        profile = await self.memory.get_company_profile(session, tenant_id, project_id)

        script_prompt = (
            f"Write a {duration_seconds}-second video script for a social media short.\n"
            f"Company: {profile.get('company_name')}\n"
            f"Niche: {profile.get('company_niche')}\n"
            f"Topic: {topic}\n"
            f"Voice: {profile.get('brand_voice')}\n"
            f"Return JSON with: script_text (str, Russian, for voiceover), "
            f"on_screen_text (str, what appears on screen), "
            f"visual_description (str), call_to_action (str)"
        )

        script_result = await ai_client.generate(prompt=script_prompt, response_format={"type": "json_object"})
        script_data = script_result if isinstance(script_result, dict) else {"script_text": str(script_result)}
        script_text = script_data.get("script_text", script_data.get("on_screen_text", ""))

        video_url = None
        if avatar_id:
            video_url = await ai_client.generate_talking_head(
                avatar_id=avatar_id,
                text=script_text,
                duration=duration_seconds,
            )

        if not video_url:
            video_url = await ai_client.generate_video(
                prompt=script_data.get("visual_description", topic),
                text=script_text,
            )

        if not video_url:
            return {
                "video_url": "",
                "script": script_data,
                "duration_seconds": duration_seconds,
                "error": "video_generation_failed",
            }

        stored_url = await storage_client.upload_from_url(video_url, f"{tenant_id}/{project_id}/videos/")

        return {
            "video_url": stored_url,
            "script": script_data,
            "duration_seconds": duration_seconds,
        }
