import asyncio
import json
import os
import sys

# Добавляем корень проекта в PYTHONPATH
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

# --- MOCKING AI CLIENT FOR SIMULATION WITHOUT KEYS ---
from backend.app.modules.automation.core.ai_client import AIClient
async def mock_generate_json(self, messages, schema, **kwargs):
    # Простейший мок возвращающий пустые поля, но валидный для Pydantic
    print(f"[MOCK AI] Generating JSON for {schema.__name__}...")
    # Инициализируем Pydantic модель с заглушками в зависимости от схемы
    mock_data = {}
    for field_name, field in schema.model_fields.items():
        if field.annotation == str:
            mock_data[field_name] = f"Mocked {field_name}"
        elif field.annotation == list[str]:
            mock_data[field_name] = [f"Mocked {field_name} 1", f"Mocked {field_name} 2"]
        else:
            mock_data[field_name] = None
    return mock_data

async def mock_generate_image(self, prompt, **kwargs):
    print(f"[MOCK AI] Generating image for prompt: {prompt}")
    return "https://mock-image-url.com/image.png"

AIClient.generate_json = mock_generate_json
AIClient.generate_image = mock_generate_image
# -----------------------------------------------------

from backend.app.modules.automation.core.orchestrator import WorkflowEngine
from backend.app.modules.automation.agents.implementations.base import AgentType

async def main():
    print("=" * 60)
    print("🚀 NEURA AI - ИМИТАЦИЯ ДЕЙСТВИЙ КЛИЕНТА (СИМУЛЯТОР)")
    print("=" * 60)
    
    # Имитация того, что клиент заполнил форму онбординга
    print("\n[Client] Заполняет форму онбординга (Business Memory)...")
    initial_context = {
        "tenant_id": "test-client-123",
        "company_name": "Зеленый Кролик",
        "industry": "Спешелти-кофейня",
        "connected_platforms": ["Instagram", "Telegram"],
        "onboarding_answers": {
            "business_strategy": "Кофейня в центре города, ориентирована на молодежь.",
            "description": "Эстетичная спешелти-кофейня с веганскими десертами.",
            "target_audience": "Зумеры, студенты, фрилансеры.",
            "tone_of_voice": "Дружелюбный, стильный, с юмором.",
            "forbidden_topics": "Политика, цены конкурентов."
        },
        "uploaded_files_summary": "PDF меню: Матча Латте, Веганский Брауни, Капучино на миндальном",
        "raw_catalog_file": "Name,Price,Category\nМатча Латте,350,Напитки\nВеганский Брауни,250,Десерты\nКапучино на миндальном,300,Напитки\nАйс Матча,400,Напитки",
        "manual_catalog_input": "Приоритет: сделай упор на веганские позиции и айс матчу на этой неделе.",
        "recent_promoted": "Матча Латте",
        "uploaded_brand_files": "Логотип в векторе, брендбук кофейни",
        "preference_model": "Подписчики реагируют на юмор и видео с рецептами",
        "queue_count": 2,
        "queue_days_ahead": 1,
        "recent_publications": "Пост про новый десерт, видео баристы",
        "top_performing_content": "Видео с процессом заваривания матчи",
        "low_performing_content": "Текстовые посты о графике работы",
        "stats": {
            "views": 25000, 
            "likes": 1200, 
            "comments": 150
        },
        "metrics": {
            "engagement_rate": "8%",
            "top_format": "Reels"
        }
    }
    
    engine = WorkflowEngine()
    
    print("\n[Simulator] Запуск полного конвейера (DAG)...")
    # Мы запустим несколько веток:
    # 1. Retail -> Packaging (Creator) -> Content -> Image -> Publisher
    # 2. Analytics -> CEO -> Training (симуляция петли обратной связи)
    
    agents_to_run = [
            AgentType.BUSINESS,
            AgentType.MARKETING,
            AgentType.BRAND,
            AgentType.TRAINING,
            AgentType.PLANNER,
            AgentType.RETAIL,
            AgentType.CONTENT,
            AgentType.PROMPT_DIRECTOR,
            AgentType.UGC_AVATAR,
            AgentType.MOTION_PRODUCT,
            AgentType.TIMELAPSE,
            AgentType.IMAGE,
            AgentType.VIDEO,
            AgentType.EDITOR,
            AgentType.PREVIEW,
            AgentType.CHECKER,
            AgentType.PUBLISHER,
            AgentType.ANALYTICS,
            AgentType.CEO
        ]
    
    result_context = await engine.execute_dag(initial_context, agents_to_run)
    
    print("\n" + "=" * 60)
    print("🎉 СИМУЛЯЦИЯ ЗАВЕРШЕНА. РЕЗУЛЬТАТЫ СОХРАНЕНЫ.")
    print("=" * 60)
    
    print("\n✅ DAG Context Keys:", list(result_context.keys()))

if __name__ == "__main__":
    asyncio.run(main())
