from typing import Any
from backend.app.modules.automation.agents.capabilities.base import Capability
from backend.app.integrations.ai_adapters import build_ai_adapter, AIGenerateRequest

class ValidateVideoCapability(Capability):
    async def execute(self, **kwargs: Any) -> Any:
        adapter = build_ai_adapter()
        video_url = kwargs.get("context", {}).get("video_url", "unknown")
        brief = kwargs.get("context", {}).get("brief", {})
        request = AIGenerateRequest(
            task_type="checker.validate_video",
            context={
                "system_prompt": "Универсальная проверка видео-контента перед публикацией. Ты эксперт по монтажу.",
                "user_prompt": f"Проверь видео по ссылке: {video_url}\nБриф:\n{brief}\nУбедись, что сцены совпадают, титры и брендинг присутствуют.",
                "response_schema": {
                    "scenes_matched": "boolean",
                    "titles_present": "boolean",
                    "branding_present": "boolean",
                    "visual_artifacts_detected": "boolean",
                    "issues": ["string"]
                }
            }
        )
        return await adapter.generate(request)
