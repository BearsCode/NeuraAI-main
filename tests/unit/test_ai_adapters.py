from __future__ import annotations

import json

import httpx
import pytest

from backend.app.integrations.ai_adapters import AIGenerateRequest, ClaudeLLMAdapter, OpenAILLMAdapter


@pytest.mark.asyncio
async def test_openai_adapter_uses_chat_completions_and_parses_json() -> None:
    requests: list[httpx.Request] = []

    def handler(request: httpx.Request) -> httpx.Response:
        requests.append(request)
        assert request.url.path == "/v1/chat/completions"
        payload = json.loads(request.content)
        assert payload["response_format"] == {"type": "json_object"}
        assert payload["messages"][0]["role"] == "system"
        return httpx.Response(
            200,
            json={
                "choices": [
                    {
                        "message": {
                            "content": json.dumps({"positioning": "clear market position"})
                        }
                    }
                ]
            },
        )

    adapter = OpenAILLMAdapter(
        api_key="test-key",
        model="gpt-test",
        base_url="https://api.example.com/v1",
        http_client_factory=lambda: httpx.AsyncClient(transport=httpx.MockTransport(handler)),
    )

    result = await adapter.generate(
        AIGenerateRequest(
            task_type="strategy_generation",
            context={
                "system_prompt": "System",
                "user_prompt": "User",
                "response_schema": {"type": "object"},
            },
        )
    )

    assert len(requests) == 1
    assert result == {"positioning": "clear market position"}


@pytest.mark.asyncio
async def test_claude_adapter_uses_messages_endpoint_and_parses_json() -> None:
    requests: list[httpx.Request] = []

    def handler(request: httpx.Request) -> httpx.Response:
        requests.append(request)
        assert request.url.path == "/v1/messages"
        payload = json.loads(request.content)
        assert payload["system"] == "System"
        assert payload["messages"][0]["role"] == "user"
        return httpx.Response(
            200,
            json={
                "content": [
                    {
                        "type": "text",
                        "text": json.dumps({"plan_summary": "strong content plan"})
                    }
                ]
            },
        )

    adapter = ClaudeLLMAdapter(
        api_key="test-key",
        model="claude-test",
        base_url="https://claude.example.com",
        http_client_factory=lambda: httpx.AsyncClient(transport=httpx.MockTransport(handler)),
    )

    result = await adapter.generate(
        AIGenerateRequest(
            task_type="content_plan_generation",
            context={
                "system_prompt": "System",
                "user_prompt": "User",
                "response_schema": {"type": "object"},
            },
        )
    )

    assert len(requests) == 1
    assert result == {"plan_summary": "strong content plan"}
