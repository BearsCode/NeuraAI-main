from typing import Any
from backend.app.modules.automation.agents.capabilities.base import Capability
from backend.app.integrations.ai_adapters import build_ai_adapter, AIGenerateRequest

class WriteCompositionCapability(Capability):
    async def execute(self, **kwargs: Any) -> Any:
        adapter = build_ai_adapter()
        request = AIGenerateRequest(
            task_type="editor.write_composition",
            context={
                "system_prompt": (
                    "Написание Remotion-композиции (.tsx) через Claude Code c Remotion Agent Skills на основе брифа.\n"
                    "ПРАВИЛА:\n"
                    "1. Используй <Sequence>, interpolate() и spring() из Remotion API.\n"
                    "2. Встраивай готовые клипы через <OffthreadVideo>.\n"
                    "3. Текст и цифры анимируй программно.\n"
                    "4. Цвета и шрифты берутся из Brand Agent.\n"
                    "5. Логотип появляется через fade-in (interpolate), не резко."
                ),
                "user_prompt": "Напиши код композиции.",
                "response_schema": {
                    "composition_code_path": "string"
                }
            }
        )
        return await adapter.generate(request)

class RenderAndQACapability(Capability):
    async def execute(self, **kwargs: Any) -> Any:
        adapter = build_ai_adapter()
        request = AIGenerateRequest(
            task_type="editor.render_and_qa",
            context={
                "system_prompt": "Рендер композиции в MP4 + QA-проверка через Gemini API.",
                "user_prompt": "Выполни рендер и проверку.",
                "response_schema": {
                    "final_video_url": "string",
                    "duration_sec": "number",
                    "scenes_used": [{"scene_number": "number", "media_source": "string"}],
                    "qa_report": {
                        "scenes_matched": "boolean",
                        "titles_present": "boolean",
                        "branding_present": "boolean",
                        "visual_artifacts_detected": "boolean",
                        "issues": ["string"]
                    }
                }
            }
        )
        return await adapter.generate(request)

class SyncCoverCapability(Capability):
    async def execute(self, **kwargs: Any) -> Any:
        adapter = build_ai_adapter()
        request = AIGenerateRequest(
            task_type="editor.sync_cover",
            context={
                "system_prompt": "Сверка обложки от Preview Agent с финальным видео, перегенерация при рассинхроне.",
                "user_prompt": "Сверь обложку с видео.",
                "response_schema": {
                    "cover_sync_status": "string"
                }
            }
        )
        return await adapter.generate(request)
