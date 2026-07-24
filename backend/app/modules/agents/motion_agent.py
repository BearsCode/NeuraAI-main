from __future__ import annotations

from typing import Any

from sqlalchemy.ext.asyncio import AsyncSession

from backend.app.integrations import ai_client, storage_client
from backend.app.modules.agents.base import BaseAgent
from backend.app.services_internal.business_memory import BusinessMemoryService


class MotionAgent(BaseAgent):
    name = "motion"
    description = "Motion-Товар Агент: Превращение фото товара в кинематографичную анимацию"

    def __init__(self):
        self.memory = BusinessMemoryService()

    async def detect_object(self, photo_url: str) -> str:
        prompt = f"Определи тип товара по фото {photo_url}. Верни JSON с полем detected_object_type."
        res = await ai_client.generate(prompt=prompt, response_format={"type": "json_object"})
        if isinstance(res, dict):
            return res.get("detected_object_type", "unknown")
        return "unknown"

    async def select_style(self, object_type: str, brand_style: dict[str, Any]) -> str:
        prompt = f"Подбери стиль анимации (вращение, левитация, slow_motion, частицы, стекло, дым, вода, свет, неон, взрыв, трансформация) для товара '{object_type}' и стиля {brand_style}. Верни JSON с полем animation_style."
        res = await ai_client.generate(prompt=prompt, response_format={"type": "json_object"})
        if isinstance(res, dict):
            return res.get("animation_style", "вращение")
        return "вращение"

    async def plan_scenes(self, object_type: str, style: str, colors: str, target_model: str) -> dict[str, Any]:
        prompt = f"""ROLE
Ты — Motion-Товар Агент платформы Нейра. Ты создаёшь премиальные рекламные видео товаров, где главный герой — сам продукт, без участия людей или AI-аватаров. Твоя задача — превратить обычное фото товара в кинематографичную анимацию.

MISSION
На основе фотографии товара из Каталога, фирменных цветов и логотипа бренда сгенерировать сценарий анимации и промпты для video-генерации, подчёркивающие премиальность и привлекательность продукта.

RULES
1. Фото товара обязательно.
2. Стиль анимации должен соответствовать типу товара.
3. Всегда заканчивай сцену показом логотипа бренда.
4. Используй фирменные цвета бренда ({colors}) в освещении и фоне сцен, где это уместно.
5. Раскадровка всегда из 5 сцен: тёмный фон → появление товара → вращение/движение → крупный план → логотип.
6. Генерируй промпты отдельно под ту video-модель, которая указана как активная ({target_model}).

INPUT DATA
Object Type: {object_type}
Style: {style}
Brand Colors: {colors}
Target Model: {target_model}

OUTPUT
JSON: {{
    "detected_object_type": "{object_type}",
    "animation_style": "{style}",
    "scenes": [
        {{ "scene_number": 1, "description": "string", "prompt": "string" }}
    ],
    "music_mood": "string",
    "target_model": "{target_model}"
}}
"""
        res = await ai_client.generate(prompt=prompt, response_format={"type": "json_object"})
        return res if isinstance(res, dict) else {}

    async def generate_scenes_video(self, scenes: list[dict[str, Any]], photo_url: str, target_model: str) -> list[str]:
        from backend.app.integrations.media_adapters import build_scene_adapter
        video_urls = []
        adapter = build_scene_adapter()
        for scene in scenes:
            url = await adapter.generate_scene(prompt=scene.get("prompt", ""), image_url=photo_url)
            if url:
                video_urls.append(url)
        return video_urls

    async def assemble_video(self, video_urls: list[str]) -> str | None:
        if not video_urls:
            return None
        return video_urls[0]

    async def execute(
        self,
        session: AsyncSession,
        input_data: dict[str, Any],
        context: dict[str, Any] | None = None,
    ) -> dict[str, Any]:
        project_id = input_data.get("project_id", (context or {}).get("project_id"))
        tenant_id = input_data.get("tenant_id", (context or {}).get("tenant_id"))
        photo_url = input_data.get("photo_url", "")
        target_model = input_data.get("target_model", "kling")

        profile = await self.memory.get_company_profile(session, tenant_id, project_id)
        brand_colors = profile.get("brand_colors", "#FFFFFF")

        # 1. Detect object
        object_type = await self.detect_object(photo_url)

        # 2. Select style
        style = await self.select_style(object_type, profile)

        # 3. Plan scenes
        scene_plan = await self.plan_scenes(object_type, style, brand_colors, target_model)
        scenes = scene_plan.get("scenes", [])

        # 4. Generate video
        video_urls = await self.generate_scenes_video(scenes, photo_url, target_model)

        # 5. Assemble video
        final_video_url = await self.assemble_video(video_urls)

        stored_url = None
        if final_video_url:
            stored_url = await storage_client.upload_from_url(final_video_url, f"{tenant_id}/{project_id}/videos/motion/")

        return {
            "video_url": stored_url,
            "scene_plan": scene_plan,
            "object_type": object_type,
            "animation_style": style
        }
