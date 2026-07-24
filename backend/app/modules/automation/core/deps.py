from functools import lru_cache
from .ai_client import AIClient
from backend.app.core.configs.settings import settings

@lru_cache
def get_ai_client() -> AIClient:
    return AIClient(
        openai_api_key=settings.openai_api_key,
        anthropic_api_key=settings.anthropic_api_key,
    )
