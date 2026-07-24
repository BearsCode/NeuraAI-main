from typing import Any
from backend.app.modules.automation.agents.capabilities.base import Capability
from backend.app.integrations.ai_adapters import build_ai_adapter, AIGenerateRequest

class AnalyzeProjectCapability(Capability):
    async def execute(self, **kwargs: Any) -> Any:
        adapter = build_ai_adapter()
        request = AIGenerateRequest(
            task_type="timelapse.analyze_project",
            context={
                "system_prompt": "Анализ входных материалов проекта (план, рендер, фото, описание) и определение ключевых характеристик.",
                "user_prompt": "Определи процесс.",
                "response_schema": {
                    "process_type": "string"
                }
            }
        )
        return await adapter.generate(request)

class BuildStagesCapability(Capability):
    async def execute(self, **kwargs: Any) -> Any:
        adapter = build_ai_adapter()
        context_data = kwargs.get("context", {})
        request = AIGenerateRequest(
            task_type="timelapse.build_stages",
            context={
                "system_prompt": (
                    "Ты — Таймлапс Агент платформы Нейра. Ты создаёшь кинематографичные визуализации "
                    "протяжённого во времени процесса создания чего-либо от начальной точки до готового результата."
                ),
                "user_prompt": (
                    f"Тип процесса: {context_data.get('process_type')}\n"
                    "Сгенерируй от 5 до 9 логичных этапов процесса. Каждый этап должен логически следовать из "
                    "предыдущего без пропусков."
                ),
                "response_schema": {
                    "stages": [
                        {
                            "stage_number": "number",
                            "title": "string",
                            "description": "string",
                            "environment_details": ["string"],
                            "camera_movement": "string"
                        }
                    ],
                    "estimated_total_duration_sec": "number"
                }
            }
        )
        return await adapter.generate(request)

class PlanCameraCapability(Capability):
    async def execute(self, **kwargs: Any) -> Any:
        adapter = build_ai_adapter()
        request = AIGenerateRequest(
            task_type="timelapse.plan_camera",
            context={
                "system_prompt": "Планирование движения камеры для каждого этапа с обеспечением разнообразия.",
                "user_prompt": "Спланируй камеру, чтобы не было более 2 одинаковых движений подряд.",
                "response_schema": {
                    "camera_plan_success": "boolean"
                }
            }
        )
        return await adapter.generate(request)

class GenerateScenesCapability(Capability):
    async def execute(self, **kwargs: Any) -> Any:
        adapter = build_ai_adapter()
        request = AIGenerateRequest(
            task_type="timelapse.generate_scenes",
            context={
                "system_prompt": "Генерация видео-сцен по каждому этапу через Kling.",
                "user_prompt": "Сгенерируй сцены.",
                "response_schema": {
                    "scene_videos": ["string"]
                }
            }
        )
        return await adapter.generate(request)

class AssembleFinalCapability(Capability):
    async def execute(self, **kwargs: Any) -> Any:
        adapter = build_ai_adapter()
        request = AIGenerateRequest(
            task_type="timelapse.assemble_final",
            context={
                "system_prompt": "Финальный монтаж — склейка этапов, музыка, титры, логотип и контакты.",
                "user_prompt": "Смонтируй таймлапс.",
                "response_schema": {
                    "video_url": "string",
                    "logo_present": "boolean",
                    "contacts_present": "boolean"
                }
            }
        )
        return await adapter.generate(request)
