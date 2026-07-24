from __future__ import annotations

from typing import Any

from sqlalchemy.ext.asyncio import AsyncSession

from backend.app.integrations import ai_client, storage_client
from backend.app.modules.agents.base import BaseAgent
from backend.app.services_internal.business_memory import BusinessMemoryService


class AvatarAgent(BaseAgent):
    name = "avatar"
    description = "UGC AI-Аватар Агент: Сценарии продающих видео с AI-аватаром"

    def __init__(self):
        self.memory = BusinessMemoryService()

    async def analyze_product(self, product_info: str) -> dict[str, Any]:
        prompt = f"Анализ товара/услуги: {product_info}. Верни JSON с полями benefits (массив) и pain_points (массив)."
        res = await ai_client.generate(prompt=prompt, response_format={"type": "json_object"})
        return res if isinstance(res, dict) else {}

    async def select_format(self, product_analysis: dict[str, Any]) -> str:
        prompt = f"Выбери формат ролика (обзор, распаковка, сравнение, отзыв, faq, топ-n, история клиента, экспертное, новинка, рекомендация) для: {product_analysis}. Верни JSON с полем suggested_format."
        res = await ai_client.generate(prompt=prompt, response_format={"type": "json_object"})
        if isinstance(res, dict):
            return res.get("suggested_format", "обзор")
        return "обзор"

    async def write_script(self, profile: dict[str, Any], product_info: str, format_: str, duration: int) -> dict[str, Any]:
        prompt = f"""ROLE
Ты — UGC AI-Аватар Агент платформы Нейра. Ты пишешь сценарии продающих видео, которые озвучивает AI-аватар бизнеса. Твоя речь должна звучать как естественное обращение живого человека к камере, а не как рекламный текст.

MISSION
На основе карточки товара/услуги из Каталога и Business Memory клиента создать сценарий короткого видео, где AI-аватар убедительно рассказывает о продукте и подводит зрителя к целевому действию.

RULES
1. Используй только факты о товаре из предоставленной карточки Каталога — никогда не выдумывай характеристики, цену или свойства, которых там нет.
2. Тон речи строго соответствует Tone of Voice из Business Memory.
3. Структура сценария обязательна: Хук → Проблема → Решение → Демонстрация → Преимущества → CTA.
4. Речь должна звучать разговорно — короткие фразы, никаких канцеляризмов и сложных конструкций.
5. Один сценарий — один товар/услуга.
6. Длительность речи должна укладываться в {duration} секунд ролика.
7. Обязательно заверши явным и конкретным призывом к действию.

INPUT DATA
Company: {profile.get('company_name')}
Voice: {profile.get('brand_voice')}
Product info: {product_info}
Selected Format: {format_}

OUTPUT
JSON: {{
    "hook": "string",
    "problem": "string",
    "solution": "string",
    "product_demo": "string",
    "benefits": ["string"],
    "cta": "string",
    "full_script": "string",
    "estimated_duration_sec": {duration},
    "suggested_format": "{format_}"
}}
"""
        res = await ai_client.generate(prompt=prompt, response_format={"type": "json_object"})
        return res if isinstance(res, dict) else {"full_script": str(res)}

    async def generate_voice(self, script_text: str, avatar_id: str) -> str | None:
        from backend.app.core.configs import settings
        import httpx
        import uuid
        if not settings.openai_api_key:
            return "https://example.com/voice_placeholder.mp3"
            
        headers = {
            "Authorization": f"Bearer {settings.openai_api_key}",
            "Content-Type": "application/json",
        }
        payload = {
            "model": "tts-1",
            "input": script_text,
            "voice": "alloy"
        }
        
        try:
            async with httpx.AsyncClient(timeout=30.0) as client:
                response = await client.post(
                    "https://api.openai.com/v1/audio/speech",
                    headers=headers,
                    json=payload
                )
                if response.status_code == 200:
                    _, url = await storage_client.store_bytes(
                        project_id="avatar_voices",
                        file_name=f"{uuid.uuid4().hex}.mp3",
                        content_type="audio/mpeg",
                        data=response.content
                    )
                    return url
        except Exception as e:
            import logging
            logging.getLogger(__name__).warning(f"Voice generation failed: {e}")
            
        return "https://example.com/voice_placeholder.mp3"

    async def generate_video(self, script_text: str, avatar_id: str | None, duration: int, prompt_visual: str) -> str | None:
        if avatar_id:
            return await ai_client.generate_talking_head(
                avatar_id=avatar_id,
                text=script_text,
                duration=duration,
            )
        else:
            return await ai_client.generate_video(
                prompt=prompt_visual,
                text=script_text,
            )

    async def execute(
        self,
        session: AsyncSession,
        input_data: dict[str, Any],
        context: dict[str, Any] | None = None,
    ) -> dict[str, Any]:
        project_id = input_data.get("project_id", (context or {}).get("project_id"))
        tenant_id = input_data.get("tenant_id", (context or {}).get("tenant_id"))
        duration_seconds = input_data.get("duration_seconds", 30)
        avatar_id = input_data.get("avatar_id")
        product_info = input_data.get("product_info", "Generic Product")

        profile = await self.memory.get_company_profile(session, tenant_id, project_id)

        # 1. Analyze product
        product_analysis = await self.analyze_product(product_info)
        
        # 2. Select format
        selected_format = await self.select_format(product_analysis)
        
        # 3. Write script
        script_data = await self.write_script(profile, product_info, selected_format, duration_seconds)
        script_text = script_data.get("full_script", script_data.get("on_screen_text", ""))
        
        # 4. Generate voice
        voice_url = await self.generate_voice(script_text, avatar_id or "")

        # 5. Generate video
        video_url = await self.generate_video(
            script_text=script_text,
            avatar_id=avatar_id,
            duration=duration_seconds,
            prompt_visual=script_data.get("product_demo", "product showcase")
        )

        stored_url = None
        if video_url:
            stored_url = await storage_client.upload_from_url(video_url, f"{tenant_id}/{project_id}/videos/avatar/")

        return {
            "video_url": stored_url,
            "voice_url": voice_url,
            "script": script_data,
            "duration_seconds": duration_seconds,
            "format": selected_format,
            "analysis": product_analysis
        }
