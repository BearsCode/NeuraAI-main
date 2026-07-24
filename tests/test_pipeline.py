import asyncio
from backend.app.modules.automation.core.orchestrator import Orchestrator

async def main():
    print("=== ЗАПУСК E2E ТЕСТА ОРКЕСТРАТОРА ===")
    orchestrator = Orchestrator()
    
    # Симуляция заказа от клиента
    result = await orchestrator.run_pipeline(
        prompt="Напиши пост про запуск новой линейки кроссовок",
        platform="Instagram"
    )
    
    print("\\n=== РЕЗУЛЬТАТ ===")
    print(result)

if __name__ == "__main__":
    asyncio.run(main())
