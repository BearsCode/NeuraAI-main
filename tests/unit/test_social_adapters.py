from __future__ import annotations

import json
from urllib.parse import parse_qs

import httpx
import pytest

from backend.app.core.configs import Settings
from backend.app.core.security import encrypt_secret
from backend.app.db.enums import IntegrationPlatform
from backend.app.db.social_integration import SocialIntegration
from backend.app.integrations.social_adapters import (
    MockSocialAdapter,
    PublishPayload,
    SocialAdapterRegistry,
    TelegramSocialAdapter,
    UnsupportedSocialAdapter,
    VKSocialAdapter,
)


def test_social_adapter_registry_uses_mock_mode_by_default() -> None:
    registry = SocialAdapterRegistry(Settings(_env_file=None, app={"env": "local"}, social={"mode": "mock"}))

    adapter = registry.adapter_for("telegram")

    assert isinstance(adapter, MockSocialAdapter)


def test_social_adapter_registry_selects_live_adapters() -> None:
    registry = SocialAdapterRegistry(Settings(_env_file=None, app={"env": "local"}, social={"mode": "live"}))

    assert isinstance(registry.adapter_for("telegram"), TelegramSocialAdapter)
    assert isinstance(registry.adapter_for("vk"), VKSocialAdapter)
    assert isinstance(registry.adapter_for("instagram"), UnsupportedSocialAdapter)


@pytest.mark.asyncio
async def test_telegram_adapter_publishes_text_message() -> None:
    requests: list[httpx.Request] = []

    def handler(request: httpx.Request) -> httpx.Response:
        requests.append(request)
        assert request.url.path == "/bottelegram-token/sendMessage"
        payload = json.loads(request.content)
        assert payload["chat_id"] == "@neyra"
        assert payload["text"] == "Launch post"
        assert payload["parse_mode"] == "HTML"
        return httpx.Response(
            200,
            json={
                "ok": True,
                "result": {
                    "message_id": 42,
                    "chat": {"id": "@neyra"},
                },
            },
        )

    adapter = TelegramSocialAdapter(
        limit_per_minute=1000,
        http_client_factory=lambda: httpx.AsyncClient(transport=httpx.MockTransport(handler)),
    )
    integration = SocialIntegration(
        tenant_id="tenant-1",
        project_id="project-1",
        platform=IntegrationPlatform.TELEGRAM,
        account_handle="@neyra",
        encrypted_access_token=encrypt_secret("telegram-token"),
        publication_settings={"parse_mode": "HTML"},
    )

    result = await adapter.publish(
        integration,
        PublishPayload(text="Launch post", media_urls=[], scheduled_at=None, metadata={}),
    )

    assert len(requests) == 1
    assert result.external_post_id == "@neyra:42"
    assert result.metadata == {
        "platform": "telegram",
        "method": "sendMessage",
        "chat_id": "@neyra",
        "message_id": "42",
    }


@pytest.mark.asyncio
async def test_vk_adapter_publishes_wall_post() -> None:
    requests: list[httpx.Request] = []

    def handler(request: httpx.Request) -> httpx.Response:
        requests.append(request)
        assert request.url.path == "/method/wall.post"
        payload = parse_qs(request.content.decode())
        assert payload["access_token"] == ["vk-token"]
        assert payload["owner_id"] == ["-123"]
        assert payload["from_group"] == ["1"]
        assert payload["message"] == ["VK post"]
        assert payload["attachments"] == ["photo-123_456"]
        return httpx.Response(200, json={"response": {"post_id": 456}})

    adapter = VKSocialAdapter(
        limit_per_minute=1000,
        http_client_factory=lambda: httpx.AsyncClient(transport=httpx.MockTransport(handler)),
    )
    integration = SocialIntegration(
        tenant_id="tenant-1",
        project_id="project-1",
        platform=IntegrationPlatform.VK,
        account_handle="club123",
        encrypted_access_token=encrypt_secret("vk-token"),
    )

    result = await adapter.publish(
        integration,
        PublishPayload(text="VK post", media_urls=["photo-123_456"], scheduled_at=None, metadata={}),
    )

    assert len(requests) == 1
    assert result.external_post_id == "-123_456"
    assert result.metadata == {
        "platform": "vk",
        "owner_id": -123,
        "post_id": 456,
    }


@pytest.mark.asyncio
async def test_unsupported_live_adapter_rejects_validation() -> None:
    registry = SocialAdapterRegistry(Settings(_env_file=None, app={"env": "local"}, social={"mode": "live"}))

    with pytest.raises(NotImplementedError, match="instagram integration is not implemented yet"):
        await registry.adapter_for("instagram").validate_connection("@neyra", "token")
