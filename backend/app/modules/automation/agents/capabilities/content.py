from typing import Any
from backend.app.modules.automation.agents.capabilities.base import Capability
from backend.app.integrations.ai_adapters import build_ai_adapter, AIGenerateRequest

class GenerateTopicsCapability(Capability):
    async def execute(self, **kwargs: Any) -> Any:
        adapter = build_ai_adapter()
        context_data = kwargs.get("context", {})
        request = AIGenerateRequest(
            task_type="content.generate_topics",
            context={
                "system_prompt": "Ты — креативный копирайтер. Придумай 5 тем постов для выбранной рубрики.",
                "user_prompt": f"Рубрика: {context_data.get('pillar')}\nКомпания: {context_data.get('company_name')}",
                "response_schema": {
                    "topics": ["string"]
                }
            }
        )
        return await adapter.generate(request)

class WritePostsCapability(Capability):
    async def execute(self, **kwargs: Any) -> Any:
        adapter = build_ai_adapter()
        context_data = kwargs.get("context", {})
        system_prompt = (
            "Ты — Content Agent платформы Нейра.\n"
            "Пишешь посты от лица бизнеса. Текст — живой, не AI-шный.\n"
            "Не начинай с клише. Цепляющее начало, мысль, CTA."
        )
        user_prompt = (
            f"КОМПАНИЯ: {context_data.get('company_name')}\n"
            f"TONE: {context_data.get('tone_of_voice')}\n"
            f"СООБЩЕНИЯ: {context_data.get('key_messages')}\n"
            f"ЗАПРЕТЫ: {context_data.get('forbidden_topics')}\n\n"
            f"ЗАДАНИЕ:\n"
            f"Рубрика: {context_data.get('pillar')}, Тема: {context_data.get('topic')}\n"
            f"Платформа: {context_data.get('platform')}, Формат: пост"
        )
        request = AIGenerateRequest(
            task_type="content.write_post",
            context={
                "system_prompt": system_prompt,
                "user_prompt": user_prompt,
                "response_schema": {
                    "text": "string",
                    "hashtags": ["string"],
                    "image_description": "string",
                    "image_mood": "string",
                    "char_count": "number"
                }
            }
        )
        return await adapter.generate(request)

class WriteStoriesCapability(Capability):
    async def execute(self, **kwargs: Any) -> Any:
        adapter = build_ai_adapter()
        context_data = kwargs.get("context", {})
        request = AIGenerateRequest(
            task_type="content.write_stories",
            context={
                "system_prompt": "Ты — сторисмейкер. Напиши сценарий из 3-5 сторис.",
                "user_prompt": f"Тема: {context_data.get('topic')}\nКомпания: {context_data.get('company_name')}",
                "response_schema": {
                    "stories": [{"frame_number": "number", "text": "string", "visual": "string"}]
                }
            }
        )
        return await adapter.generate(request)

class WriteReelsCapability(Capability):
    async def execute(self, **kwargs: Any) -> Any:
        adapter = build_ai_adapter()
        context_data = kwargs.get("context", {})
        request = AIGenerateRequest(
            task_type="content.write_reels",
            context={
                "system_prompt": "Ты — сценарист коротких видео (Reels/Shorts/TikTok).",
                "user_prompt": f"Тема: {context_data.get('topic')}\nДлина: 30-60 сек. Напиши хук, тело и CTA.",
                "response_schema": {
                    "script": "string",
                    "hook": "string",
                    "cta": "string",
                    "format": "string"
                }
            }
        )
        return await adapter.generate(request)

class GenerateCTA(Capability):
    async def execute(self, **kwargs: Any) -> Any:
        adapter = build_ai_adapter()
        context_data = kwargs.get("context", {})
        request = AIGenerateRequest(
            task_type="content.generate_cta",
            context={
                "system_prompt": "Ты — маркетолог. Придумай сильный призыв к действию (CTA).",
                "user_prompt": f"Цель: {context_data.get('goal', 'Продажи')}",
                "response_schema": {
                    "cta": "string"
                }
            }
        )
        return await adapter.generate(request)
