from typing import Any
from backend.app.modules.automation.agents.capabilities.base import Capability
from backend.app.integrations.ai_adapters import build_ai_adapter, AIGenerateRequest

class CreateAvatarCapability(Capability):
    async def execute(self, **kwargs: Any) -> Any:
        adapter = build_ai_adapter()
        context_data = kwargs.get("context", {})
        request = AIGenerateRequest(
            task_type="video.create_avatar",
            context={
                "system_prompt": "Ты — специалист по AI-аватарам. Опиши параметры идеального цифрового аватара для бренда.",
                "user_prompt": f"Бренд: {context_data.get('company_name')}",
                "response_schema": {
                    "avatar_gender": "string",
                    "avatar_style": "string",
                    "voice_type": "string"
                }
            }
        )
        return await adapter.generate(request)

from backend.app.integrations.media_adapters import build_video_adapter

class GenerateVideoCapability(Capability):
    async def execute(self, **kwargs: Any) -> Any:
        adapter = build_ai_adapter()
        context_data = kwargs.get("context", {})
        system_prompt = (
            "Ты — Video Agent платформы Нейра.\n"
            "Напиши скрипт для talking head видео."
        )
        user_prompt = (
            f"Тема: {context_data.get('topic')}, Рубрика: {context_data.get('pillar')}\n"
            f"Платформа: {context_data.get('platform')}, Длина: {context_data.get('target_duration_sec', 30)} сек\n"
            f"Tone: {context_data.get('tone_of_voice')}, Имя: {context_data.get('owner_name')}\n"
            f"ПРАВИЛА:\n"
            f"— От 1-го лица, первые 3 сек — крючок\n"
            f"— Живой язык, паузы\n"
            f"— CTA в конце"
        )
        request = AIGenerateRequest(
            task_type="video.generate_video",
            context={
                "system_prompt": system_prompt,
                "user_prompt": user_prompt,
                "response_schema": {
                    "script": "string",
                    "hook": "string",
                    "cta": "string",
                    "word_count": "number",
                    "estimated_duration_sec": "number",
                    "format": "string",
                    "avatar_id": "string",
                    "voice_id": "string"
                }
            }
        )
        ai_response = await adapter.generate(request)
        
        vid_adapter = build_video_adapter()
        video_id = await vid_adapter.generate_video(
            script=ai_response.payload.get("script", "Hello!"),
            avatar_id=ai_response.payload.get("avatar_id", "default_avatar"),
            voice_id=ai_response.payload.get("voice_id", "default_voice")
        )
        
        ai_response.payload["video_id"] = video_id
        return ai_response

class AddVoiceCapability(Capability):
    async def execute(self, **kwargs: Any) -> Any:
        adapter = build_ai_adapter()
        context_data = kwargs.get("context", {})
        request = AIGenerateRequest(
            task_type="video.add_voice",
            context={
                "system_prompt": "Ты — звукорежиссёр. Выбери подходящий голос (TTS) и настроение.",
                "user_prompt": f"Текст: {context_data.get('script')}",
                "response_schema": {
                    "voice_id": "string",
                    "emotion": "string",
                    "pacing": "string"
                }
            }
        )
        return await adapter.generate(request)

class AddSubtitlesCapability(Capability):
    async def execute(self, **kwargs: Any) -> Any:
        adapter = build_ai_adapter()
        context_data = kwargs.get("context", {})
        request = AIGenerateRequest(
            task_type="video.add_subtitles",
            context={
                "system_prompt": "Ты — видеомонтажёр. Предложи стиль субтитров (шрифт, цвет) на основе бренда.",
                "user_prompt": f"Бренд-цвета: {context_data.get('color_palette')}",
                "response_schema": {
                    "font_family": "string",
                    "primary_color": "string",
                    "highlight_color": "string",
                    "animation_style": "string"
                }
            }
        )
        return await adapter.generate(request)
