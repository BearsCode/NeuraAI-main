from __future__ import annotations

from time import monotonic

import httpx
from fastapi import HTTPException, status

from backend.app.core.configs import settings
from backend.app.infra.circuit_breaker import CircuitBreaker
from backend.app.infra.retry import async_retry
from backend.app.observability.logging import get_logger

logger = get_logger(__name__)


class AITextService:
    def __init__(self) -> None:
        self._breaker = CircuitBreaker(
            failure_threshold=settings.ai.circuit_breaker_failures,
            reset_timeout_seconds=settings.ai.circuit_breaker_reset_seconds,
        )

    async def generate_text(
        self,
        system_prompt: str,
        user_prompt: str,
        temperature: float = 0.7,
    ) -> str:
        if not settings.ai.has_active_credentials:
            logger.warning("ai_text_mock_fallback")
            return self._mock_response(user_prompt)

        try:
            return await self._breaker.call(
                lambda: async_retry(
                    lambda: self._invoke(system_prompt, user_prompt, temperature),
                    retries=settings.workers.max_retries,
                    base_delay_seconds=1.0,
                )
            )
        except RuntimeError:
            logger.warning("ai_text_circuit_open_fallback_to_mock")
            return self._mock_response(user_prompt)
        except httpx.TimeoutException:
            raise HTTPException(
                status_code=status.HTTP_504_GATEWAY_TIMEOUT,
                detail="AI-сервис не отвечает. Попробуйте позже.",
            )
        except httpx.HTTPStatusError as e:
            logger.error("ai_text_http_error", status_code=e.response.status_code, body=e.response.text)
            raise HTTPException(
                status_code=status.HTTP_502_BAD_GATEWAY,
                detail="Ошибка AI-сервиса.",
            )
        except Exception as e:
            logger.error("ai_text_error", error=str(e))
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="Внутренняя ошибка сервера.",
            )

    async def _invoke(self, system_prompt: str, user_prompt: str, temperature: float) -> str:
        cfg = settings.ai.openai
        base_url = (cfg.base_url or "https://api.openai.com/v1").rstrip("/")
        model = cfg.model or "gpt-4o-mini"
        api_key = cfg.api_key.get_secret_value() if cfg.api_key else ""

        start = monotonic()
        async with httpx.AsyncClient(timeout=settings.ai.request_timeout_seconds) as client:
            response = await client.post(
                f"{base_url}/chat/completions",
                headers={
                    "Authorization": f"Bearer {api_key}",
                    "Content-Type": "application/json",
                },
                json={
                    "model": model,
                    "messages": [
                        {"role": "system", "content": system_prompt},
                        {"role": "user", "content": user_prompt},
                    ],
                    "temperature": temperature,
                    "stream": False,
                },
            )
            response.raise_for_status()
            data = response.json()
            elapsed = int((monotonic() - start) * 1000)
            logger.info("ai_text_invoke_ok", model=model, latency_ms=elapsed)

        return data["choices"][0]["message"]["content"]

    def _mock_response(self, user_prompt: str) -> str:
        return (
            "Сгенерированный текст:\n\n"
            f"{user_prompt[:100]}…\n\n"
            "Это тестовый ответ — AI-провайдер не настроен. "
            "Добавьте AI__OPENAI__API_KEY в .env для реальной генерации."
        )
