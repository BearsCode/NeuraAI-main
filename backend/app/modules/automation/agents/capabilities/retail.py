from typing import Any
from backend.app.modules.automation.agents.capabilities.base import Capability
from backend.app.integrations.ai_adapters import build_ai_adapter, AIGenerateRequest

class BuildCatalogCapability(Capability):
    """
    Retail Agent теперь — фоновый процесс наполнения Business Memory (Стратегии).
    Обрабатывает загруженные файлы или ручной ввод (фото/текст меню) 
    и формирует стандартизированный каталог для дальнейшего использования AI Planner.
    """
    async def execute(self, **kwargs: Any) -> Any:
        adapter = build_ai_adapter()
        context_data = kwargs.get("context", {})
        
        raw_file = context_data.get("raw_catalog_file", "")
        manual_input = context_data.get("manual_catalog_input", "")
        
        # Если нет новых данных для каталога, но каталог уже есть - просто возвращаем пустой результат
        if not raw_file and not manual_input:
            if "retail_catalog" in context_data:
                return None
            else:
                raw_file = "Данных нет"
                
        request = AIGenerateRequest(
            task_type="retail.build_catalog",
            context={
                "system_prompt": "Ты — Retail Agent платформы Нейра. Твоя задача — извлечь товары/услуги/меню из сырого текста загруженного файла или ручного ввода и сформировать структурированный каталог.",
                "user_prompt": (
                    f"Сырые данные из файла:\n{raw_file}\n\n"
                    f"Ручной ввод (текст или распознанное фото меню):\n{manual_input}\n\n"
                    f"Сформируй список товаров. Для каждого укажи точное название, логичную категорию, цену (число), привлекательное описание (дополни его сам, если нужно) и теги."
                ),
                "response_schema": {
                    "retail_catalog": [
                        {
                            "name": "string",
                            "category": "string",
                            "price": "number",
                            "description": "string",
                            "tags": ["string"]
                        }
                    ]
                }
            }
        )
        return await adapter.generate(request)
