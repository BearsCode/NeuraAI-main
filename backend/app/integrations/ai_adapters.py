from __future__ import annotations

import json
from abc import ABC, abstractmethod
from collections.abc import Callable
from dataclasses import dataclass
from typing import Any
import asyncio

import httpx

from backend.app.core.configs import settings
from backend.app.infra.circuit_breaker import CircuitBreaker
from backend.app.infra.retry import async_retry
from backend.app.observability.logging import get_logger

logger = get_logger(__name__)
HttpClientFactory = Callable[[], httpx.AsyncClient]


@dataclass(slots=True)
class AIUsage:
    prompt_tokens: int
    completion_tokens: int
    total_tokens: int
    cost_usd: float

@dataclass(slots=True)
class AIGenerateResponse:
    payload: dict[str, Any]
    usage: AIUsage
    latency_ms: int
    model_used: str
    provider: str

@dataclass(slots=True)
class AIGenerateRequest:
    task_type: str
    context: dict[str, Any]


class BaseLLMAdapter(ABC):
    @abstractmethod
    async def generate(self, request: AIGenerateRequest) -> AIGenerateResponse:
        """Generate structured output for a domain task."""


class MockLLMAdapter(BaseLLMAdapter):
    async def generate(self, request: AIGenerateRequest) -> AIGenerateResponse:
        import time
        start = time.time()
        
        company_name = str(request.context.get("company_name") or "Business")
        audience = str(request.context.get("target_audience") or "SMB audience")
        industry = str(request.context.get("industry") or "services")
        
        payload = {}
        if "content_plan" in request.task_type:
            period_days = int(request.context.get("period_days") or 30)
            platforms = _parse_platforms(request.context.get("platforms"))
            content_types = _parse_content_types(request.context.get("content_types"))
            posts: list[dict[str, Any]] = []
            for day in range(1, period_days + 1):
                platform = platforms[(day - 1) % len(platforms)]
                content_type = content_types[(day - 1) % len(content_types)]
                posts.append(
                    {
                        "day_number": day,
                        "title": f"{company_name}: day {day} {content_type} for {platform}",
                        "angle": f"Show measurable value for {audience} in {industry}.",
                        "platform": platform,
                        "content_type": content_type,
                        "media_type": "image" if content_type in {"post", "carousel"} else "video",
                        "caption": (
                            f"{company_name} helps {audience} get predictable growth with "
                            f"practical {industry} insights. Day {day} focuses on a usable next step."
                        ),
                        "call_to_action": "Book a strategy session",
                        "publish_time": "10:30",
                        "image_prompt": f"Clean editorial visual about {industry} growth for SMB teams.",
                    }
                )
            payload = {
                "plan_summary": f"30-day plan for {company_name} centered on education, proof, and offers.",
                "posts": posts,
            }
        elif "optimization" in request.task_type:
            payload = {
                "summary": f"Shift {company_name} content mix toward case-driven and educational posts.",
                "details": {
                    "reason": request.context.get("reason") or "weekly_review",
                    "best_windows": ["10:30", "18:00"],
                    "content_mix": ["45% educational", "35% case studies", "20% offer posts"],
                },
                "suggested_publish_time": "10:30",
                "suggested_frequency": "5 posts per week",
            }
        else:
            schema = request.context.get("response_schema", {})
            if schema:
                # Dynamic mock based on schema
                def mock_from_schema(s):
                    if isinstance(s, dict):
                        return {k: mock_from_schema(v) for k, v in s.items()}
                    elif isinstance(s, list):
                        return [mock_from_schema(s[0])] if s else []
                    elif s == "string":
                        return "mock_string"
                    elif s == "number":
                        return 42
                    elif s == "boolean":
                        return True
                    return None
                payload = mock_from_schema(schema)
            else:
                payload = {
                    "business_analysis": [
                        f"{company_name} operates in {industry} with a differentiated positioning opportunity.",
                        f"Messaging should anchor around fast ROI for {audience}.",
                    ],
                    "market_analysis": [
                        "Demand is strongest for predictable lead generation and content systems.",
                        "Trust signals and real client cases outperform generic branding claims.",
                    ],
                    "competitor_analysis": [
                        "Competitors usually separate analytics, scheduling, and AI generation into different tools.",
                        "An integrated workflow creates a speed-to-market advantage.",
                    ],
                    "positioning": f"{company_name} as an AI-driven outsourced marketing team for {industry}.",
                    "content_pillars": ["cases", "education", "behind the scenes", "offers"],
                    "channels": request.context.get("channels") or ["telegram", "vk"],
                    "publishing_frequency": "5 posts per week",
                    "recommendations": [
                        "Keep approval manual for sales-heavy posts.",
                        "Repurpose best Telegram posts into VK carousels.",
                    ],
                    "optimization_mode": "manual_confirmation",
                }

        usage = AIUsage(prompt_tokens=150, completion_tokens=300, total_tokens=450, cost_usd=0.001)
        return AIGenerateResponse(
            payload=payload,
            usage=usage,
            latency_ms=int((time.time() - start) * 1000),
            model_used="mock-model",
            provider="mock"
        )


class GatewayLLMAdapter(BaseLLMAdapter):
    def __init__(self, *, provider: str, base_url: str, api_key: str, model: str | None) -> None:
        self.provider = provider
        self.base_url = base_url.rstrip("/")
        self.api_key = api_key
        self.model = model
        self.breaker: CircuitBreaker[dict[str, Any]] = CircuitBreaker(
            failure_threshold=settings.ai.circuit_breaker_failures,
            reset_timeout_seconds=settings.ai.circuit_breaker_reset_seconds,
        )

    async def generate(self, request: AIGenerateRequest) -> AIGenerateResponse:
        return await self.breaker.call(
            lambda: async_retry(
                lambda: self._invoke(request),
                retries=settings.workers.max_retries,
            )
        )

    async def _invoke(self, request: AIGenerateRequest) -> AIGenerateResponse:
        import time
        start = time.time()
        async with httpx.AsyncClient(timeout=settings.ai.request_timeout_seconds) as client:
            response = await client.post(
                f"{self.base_url}/generate",
                headers={
                    "Authorization": f"Bearer {self.api_key}",
                    "Content-Type": "application/json",
                    "X-Provider": self.provider,
                },
                json={
                    "model": self.model,
                    "task_type": request.task_type,
                    "context": request.context,
                },
            )
            response.raise_for_status()
            payload = response.json()
            if not isinstance(payload, dict):
                raise ValueError("LLM gateway returned non-object JSON payload")
            
            usage = AIUsage(prompt_tokens=0, completion_tokens=0, total_tokens=0, cost_usd=0.0)
            return AIGenerateResponse(
                payload=payload,
                usage=usage,
                latency_ms=int((time.time() - start) * 1000),
                model_used=self.model or "unknown",
                provider=self.provider
            )


class OpenAILLMAdapter(BaseLLMAdapter):
    """Direct OpenAI Chat Completions adapter for structured JSON tasks."""

    def __init__(
        self,
        *,
        api_key: str,
        model: str | None,
        base_url: str | None = None,
        http_client_factory: HttpClientFactory | None = None,
    ) -> None:
        self.api_key = api_key
        self.model = model or "gpt-4o-mini"
        self.base_url = (base_url or "https://api.openai.com/v1").rstrip("/")
        self._http_client_factory = http_client_factory or self._http_client
        self.breaker: CircuitBreaker[dict[str, Any]] = CircuitBreaker(
            failure_threshold=settings.ai.circuit_breaker_failures,
            reset_timeout_seconds=settings.ai.circuit_breaker_reset_seconds,
        )

    async def generate(self, request: AIGenerateRequest) -> AIGenerateResponse:
        return await self.breaker.call(
            lambda: async_retry(lambda: self._invoke(request), retries=settings.workers.max_retries)
        )

    async def _invoke(self, request: AIGenerateRequest) -> AIGenerateResponse:
        import time
        start = time.time()
        async with self._http_client_factory() as client:
            response = await client.post(
                f"{self.base_url}/chat/completions",
                headers={
                    "Authorization": f"Bearer {self.api_key}",
                    "Content-Type": "application/json",
                },
                json={
                    "model": self.model,
                    "response_format": {"type": "json_object"},
                    "messages": [
                        {"role": "system", "content": str(request.context.get("system_prompt") or "")},
                        {"role": "user", "content": _user_prompt_with_schema(request)},
                    ],
                },
            )
            response.raise_for_status()
            payload = response.json()
        
        content = payload["choices"][0]["message"]["content"]
        parsed_payload = _parse_json_object(content, "OpenAI")
        
        # Extract usage
        raw_usage = payload.get("usage", {})
        prompt_tokens = raw_usage.get("prompt_tokens", 0)
        completion_tokens = raw_usage.get("completion_tokens", 0)
        total_tokens = raw_usage.get("total_tokens", 0)
        
        # Approximate cost for gpt-4o-mini ($0.150 / 1M prompt, $0.600 / 1M completion)
        cost = (prompt_tokens * 0.150 / 1000000) + (completion_tokens * 0.600 / 1000000)
        
        usage = AIUsage(prompt_tokens=prompt_tokens, completion_tokens=completion_tokens, total_tokens=total_tokens, cost_usd=cost)
        
        return AIGenerateResponse(
            payload=parsed_payload,
            usage=usage,
            latency_ms=int((time.time() - start) * 1000),
            model_used=self.model,
            provider="openai"
        )

    def _http_client(self) -> httpx.AsyncClient:
        return httpx.AsyncClient(timeout=settings.ai.request_timeout_seconds)


class ClaudeLLMAdapter(BaseLLMAdapter):
    """Direct Anthropic Claude adapter for structured JSON tasks."""

    def __init__(
        self,
        *,
        api_key: str,
        model: str | None,
        base_url: str | None = None,
        http_client_factory: HttpClientFactory | None = None,
    ) -> None:
        self.api_key = api_key
        self.model = model or "claude-3-5-sonnet-latest"
        self.base_url = (base_url or "https://api.anthropic.com").rstrip("/")
        self._http_client_factory = http_client_factory or self._http_client
        self.breaker: CircuitBreaker[dict[str, Any]] = CircuitBreaker(
            failure_threshold=settings.ai.circuit_breaker_failures,
            reset_timeout_seconds=settings.ai.circuit_breaker_reset_seconds,
        )

    async def generate(self, request: AIGenerateRequest) -> AIGenerateResponse:
        return await self.breaker.call(
            lambda: async_retry(lambda: self._invoke(request), retries=settings.workers.max_retries)
        )

    async def _invoke(self, request: AIGenerateRequest) -> AIGenerateResponse:
        import time
        start = time.time()
        async with self._http_client_factory() as client:
            response = await client.post(
                f"{self.base_url}/v1/messages",
                headers={
                    "x-api-key": self.api_key,
                    "anthropic-version": "2023-06-01",
                    "Content-Type": "application/json",
                },
                json={
                    "model": self.model,
                    "max_tokens": 4000,
                    "system": str(request.context.get("system_prompt") or ""),
                    "messages": [{"role": "user", "content": _user_prompt_with_schema(request)}],
                },
            )
            response.raise_for_status()
            payload = response.json()
            
        content_blocks = payload.get("content") or []
        text = "".join(str(block.get("text") or "") for block in content_blocks if block.get("type") == "text")
        parsed_payload = _parse_json_object(text, "Claude")
        
        # Extract usage
        raw_usage = payload.get("usage", {})
        prompt_tokens = raw_usage.get("input_tokens", 0)
        completion_tokens = raw_usage.get("output_tokens", 0)
        total_tokens = prompt_tokens + completion_tokens
        
        # Approximate cost for claude-3-5-sonnet ($3.00 / 1M prompt, $15.00 / 1M completion)
        cost = (prompt_tokens * 3.0 / 1000000) + (completion_tokens * 15.0 / 1000000)
        
        usage = AIUsage(prompt_tokens=prompt_tokens, completion_tokens=completion_tokens, total_tokens=total_tokens, cost_usd=cost)
        
        return AIGenerateResponse(
            payload=parsed_payload,
            usage=usage,
            latency_ms=int((time.time() - start) * 1000),
            model_used=self.model,
            provider="claude"
        )

    def _http_client(self) -> httpx.AsyncClient:
        return httpx.AsyncClient(timeout=settings.ai.request_timeout_seconds)

class GeminiLLMAdapter(BaseLLMAdapter):
    """Direct Google Gemini adapter for structured JSON tasks."""

    def __init__(
        self,
        *,
        api_key: str,
        model: str | None,
        base_url: str | None = None,
        http_client_factory: HttpClientFactory | None = None,
    ) -> None:
        self.api_key = api_key
        self.model = model or "gemini-2.0-flash"
        self.base_url = (base_url or "https://generativelanguage.googleapis.com/v1beta").rstrip("/")
        self._http_client_factory = http_client_factory or self._http_client
        self.breaker: CircuitBreaker[dict[str, Any]] = CircuitBreaker(
            failure_threshold=settings.ai.circuit_breaker_failures,
            reset_timeout_seconds=settings.ai.circuit_breaker_reset_seconds,
        )

    async def generate(self, request: AIGenerateRequest) -> AIGenerateResponse:
        return await self.breaker.call(
            lambda: async_retry(lambda: self._invoke(request), retries=settings.workers.max_retries)
        )

    async def _invoke(self, request: AIGenerateRequest) -> AIGenerateResponse:
        import time
        from backend.app.core.redis import get_redis_client
        from backend.app.infra.rate_limit import OutboundRateLimiter
        start = time.time()
        
        redis_client = get_redis_client()
        limiter = OutboundRateLimiter(redis_client)
        # Use Rate Limiter instead of hardcoded 10s sleep
        # Gemini free tier limit is 15 requests per minute (60s)
        await limiter.wait_for_token("gemini_outbound_limit", limit=15, window_seconds=60)
        
        system_text = str(request.context.get("system_prompt") or "")
        user_text = _user_prompt_with_schema(request)
        
        payload_data = {
            "contents": [{"parts": [{"text": user_text}]}],
            "generationConfig": {"responseMimeType": "application/json"}
        }
        if system_text:
            payload_data["system_instruction"] = {"parts": [{"text": system_text}]}
            
        async with self._http_client_factory() as client:
            try:
                response = await client.post(
                    f"{self.base_url}/models/{self.model}:generateContent?key={self.api_key}",
                    headers={"Content-Type": "application/json"},
                    json=payload_data,
                )
                response.raise_for_status()
            except httpx.HTTPStatusError as exc:
                if exc.response.status_code == 429:
                    logger.warning("Gemini 429 hit. Sleeping 30s and retrying...", extra={"model": self.model})
                    await asyncio.sleep(30)
                    response = await client.post(
                        f"{self.base_url}/models/{self.model}:generateContent?key={self.api_key}",
                        headers={"Content-Type": "application/json"},
                        json=payload_data,
                    )
                    response.raise_for_status()
                else:
                    raise
            payload = response.json()
            
        content = payload.get("candidates", [{}])[0].get("content", {}).get("parts", [{}])[0].get("text", "")
        parsed_payload = _parse_json_object(content, "Gemini")
        
        # Extract usage
        usage_meta = payload.get("usageMetadata", {})
        prompt_tokens = usage_meta.get("promptTokenCount", 0)
        completion_tokens = usage_meta.get("candidatesTokenCount", 0)
        total_tokens = usage_meta.get("totalTokenCount", 0)
        
        # Approximate cost for gemini-1.5-pro ($3.50 / 1M prompt, $10.50 / 1M completion)
        cost = (prompt_tokens * 3.50 / 1000000) + (completion_tokens * 10.50 / 1000000)
        
        usage = AIUsage(prompt_tokens=prompt_tokens, completion_tokens=completion_tokens, total_tokens=total_tokens, cost_usd=cost)
        
        return AIGenerateResponse(
            payload=parsed_payload,
            usage=usage,
            latency_ms=int((time.time() - start) * 1000),
            model_used=self.model,
            provider="gemini"
        )

    def _http_client(self) -> httpx.AsyncClient:
        return httpx.AsyncClient(timeout=settings.ai.request_timeout_seconds)


def build_ai_adapter() -> BaseLLMAdapter:
    if settings.ai.provider == "mock":
        return MockLLMAdapter()

    provider_credentials = getattr(settings.ai, settings.ai.provider)
    if not provider_credentials.api_key:
        logger.warning(
            "llm_provider_not_configured_falling_back_to_mock",
            extra={"provider": settings.ai.provider},
        )
        return MockLLMAdapter()

    api_key = provider_credentials.api_key.get_secret_value()
    if settings.ai.provider == "openai":
        return OpenAILLMAdapter(
            api_key=api_key,
            model=provider_credentials.model,
            base_url=provider_credentials.base_url,
        )
    if settings.ai.provider == "claude":
        return ClaudeLLMAdapter(
            api_key=api_key,
            model=provider_credentials.model,
            base_url=provider_credentials.base_url,
        )
    if settings.ai.provider == "gemini":
        return GeminiLLMAdapter(
            api_key=api_key,
            model=provider_credentials.model,
            base_url=provider_credentials.base_url,
        )

    if not provider_credentials.base_url:
        logger.warning(
            "llm_gateway_not_configured_falling_back_to_mock",
            extra={"provider": settings.ai.provider},
        )
        return MockLLMAdapter()

    return GatewayLLMAdapter(
        provider=settings.ai.provider,
        base_url=provider_credentials.base_url,
        api_key=api_key,
        model=provider_credentials.model,
    )


def _user_prompt_with_schema(request: AIGenerateRequest) -> str:
    prompt = str(request.context.get("user_prompt") or "")
    schema = request.context.get("response_schema")
    if not schema:
        return prompt
    return f"{prompt}\n\nReturn only JSON matching this schema:\n{json.dumps(schema, ensure_ascii=False)}"


def _parse_json_object(value: str, provider: str) -> dict[str, Any]:
    try:
        parsed = json.loads(value)
    except json.JSONDecodeError as exc:
        raise ValueError(f"{provider} returned invalid JSON") from exc
    if not isinstance(parsed, dict):
        raise ValueError(f"{provider} returned non-object JSON")
    return parsed


def _parse_platforms(value: Any) -> list[str]:
    if isinstance(value, str) and value.strip():
        parts = [item.strip() for item in value.split(",") if item.strip()]
        return parts or ["telegram", "vk"]
    if isinstance(value, list) and value:
        return [str(item) for item in value]
    return ["telegram", "vk"]


def _parse_content_types(value: Any) -> list[str]:
    if isinstance(value, str) and value.strip():
        parts = [item.strip() for item in value.split(",") if item.strip()]
        return parts or ["post", "carousel"]
    if isinstance(value, list) and value:
        return [str(item) for item in value]
    return ["post", "carousel"]
