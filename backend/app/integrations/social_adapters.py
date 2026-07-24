from __future__ import annotations

import asyncio
from abc import ABC, abstractmethod
from collections.abc import Callable
from collections import deque
from dataclasses import dataclass
from datetime import UTC, datetime, timedelta
from hashlib import sha256
from typing import Any

import httpx

from backend.app.core.configs import Settings, settings
from backend.app.core.security import decrypt_secret
from backend.app.db.social_integration import SocialIntegration
from backend.app.infra.circuit_breaker import CircuitBreaker
from backend.app.infra.retry import async_retry

HttpClientFactory = Callable[[], httpx.AsyncClient]

TELEGRAM_API_BASE = "https://api.telegram.org"
VK_API_BASE = "https://api.vk.com/method"
VK_API_VERSION = "5.199"


@dataclass(slots=True)
class PublishPayload:
    text: str
    media_urls: list[str]
    scheduled_at: datetime | None
    metadata: dict[str, Any]


@dataclass(slots=True)
class PublishResult:
    external_post_id: str
    published_at: datetime
    metadata: dict[str, Any]


@dataclass(slots=True)
class AnalyticsResult:
    reach: int
    followers: int
    likes: int
    comments: int
    saves: int


class AsyncRateGate:
    def __init__(self, limit_per_minute: int) -> None:
        self.limit_per_minute = limit_per_minute
        self.timestamps: deque[datetime] = deque()
        self._lock = asyncio.Lock()

    async def acquire(self) -> None:
        async with self._lock:
            now = datetime.now(UTC)
            while self.timestamps and (now - self.timestamps[0]) > timedelta(minutes=1):
                self.timestamps.popleft()
            if len(self.timestamps) >= self.limit_per_minute:
                wait_for = 60 - int((now - self.timestamps[0]).total_seconds())
                await asyncio.sleep(max(wait_for, 1))
            self.timestamps.append(datetime.now(UTC))


class BaseSocialAdapter(ABC):
    def __init__(self, platform: str, limit_per_minute: int) -> None:
        self.platform = platform
        self.gate = AsyncRateGate(limit_per_minute=limit_per_minute)
        self.breaker: CircuitBreaker[Any] = CircuitBreaker(
            failure_threshold=5,
            reset_timeout_seconds=60,
        )

    async def publish(self, integration: SocialIntegration, payload: PublishPayload) -> PublishResult:
        await self.gate.acquire()
        return await self.breaker.call(
            lambda: async_retry(
                lambda: self._publish_impl(integration, payload),
                retries=settings.workers.max_retries,
            )
        )

    async def delete(self, integration: SocialIntegration, external_post_id: str) -> None:
        await self.gate.acquire()
        await self.breaker.call(
            lambda: async_retry(
                lambda: self._delete_impl(integration, external_post_id),
                retries=settings.workers.max_retries,
            )
        )

    async def fetch_analytics(self, integration: SocialIntegration) -> AnalyticsResult:
        await self.gate.acquire()
        return await self.breaker.call(
            lambda: async_retry(
                lambda: self._fetch_analytics_impl(integration),
                retries=settings.workers.max_retries,
            )
        )

    async def validate_connection(self, account_handle: str, access_token: str) -> None:
        """Validate credentials before persisting them."""
        return None

    @abstractmethod
    async def _publish_impl(self, integration: SocialIntegration, payload: PublishPayload) -> PublishResult:
        """Publish content to a social platform."""

    @abstractmethod
    async def _delete_impl(self, integration: SocialIntegration, external_post_id: str) -> None:
        """Remove a previously published post."""

    @abstractmethod
    async def _fetch_analytics_impl(self, integration: SocialIntegration) -> AnalyticsResult:
        """Collect platform metrics."""


class MockSocialAdapter(BaseSocialAdapter):
    async def _publish_impl(self, integration: SocialIntegration, payload: PublishPayload) -> PublishResult:
        external_post_id = sha256(
            f"{self.platform}:{integration.account_handle}:{payload.text[:64]}".encode("utf-8")
        ).hexdigest()[:18]
        return PublishResult(
            external_post_id=external_post_id,
            published_at=datetime.now(UTC),
            metadata={
                "platform": self.platform,
                "media_count": len(payload.media_urls),
                "scheduled_at": payload.scheduled_at.isoformat() if payload.scheduled_at else None,
            },
        )

    async def _delete_impl(self, integration: SocialIntegration, external_post_id: str) -> None:
        return None

    async def _fetch_analytics_impl(self, integration: SocialIntegration) -> AnalyticsResult:
        seed = int(
            sha256(f"{self.platform}:{integration.account_handle}".encode("utf-8")).hexdigest()[:8],
            16,
        )
        followers = 1000 + (seed % 4000)
        likes = 50 + (seed % 300)
        comments = 5 + (seed % 70)
        saves = 3 + (seed % 50)
        return AnalyticsResult(
            reach=followers * 3,
            followers=followers,
            likes=likes,
            comments=comments,
            saves=saves,
        )


class TelegramSocialAdapter(BaseSocialAdapter):
    def __init__(
        self,
        *,
        limit_per_minute: int,
        http_client_factory: HttpClientFactory | None = None,
    ) -> None:
        super().__init__(platform="telegram", limit_per_minute=limit_per_minute)
        self._http_client_factory = http_client_factory or _default_http_client

    async def validate_connection(self, account_handle: str, access_token: str) -> None:
        await self._telegram_request(access_token, "getMe", {})

    async def _publish_impl(self, integration: SocialIntegration, payload: PublishPayload) -> PublishResult:
        token = _integration_access_token(integration, self.platform)
        request_payload = self._telegram_publish_payload(integration, payload)
        method = "sendPhoto" if payload.media_urls else "sendMessage"
        result = await self._telegram_request(token, method, request_payload)
        message_id = result.get("message_id")
        if message_id is None:
            raise RuntimeError("Telegram response does not contain message_id")

        chat_id = result.get("chat", {}).get("id", integration.account_handle)
        external_post_id = f"{chat_id}:{message_id}"
        return PublishResult(
            external_post_id=external_post_id,
            published_at=datetime.now(UTC),
            metadata={
                "platform": self.platform,
                "method": method,
                "chat_id": str(chat_id),
                "message_id": str(message_id),
            },
        )

    async def _delete_impl(self, integration: SocialIntegration, external_post_id: str) -> None:
        token = _integration_access_token(integration, self.platform)
        chat_id, message_id = _split_telegram_external_id(external_post_id, integration.account_handle)
        await self._telegram_request(
            token,
            "deleteMessage",
            {
                "chat_id": chat_id,
                "message_id": int(message_id),
            },
        )

    async def _fetch_analytics_impl(self, integration: SocialIntegration) -> AnalyticsResult:
        token = _integration_access_token(integration, self.platform)
        result = await self._telegram_request(
            token,
            "getChatMemberCount",
            {"chat_id": integration.account_handle},
        )
        followers = int(result)
        return AnalyticsResult(
            reach=followers,
            followers=followers,
            likes=0,
            comments=0,
            saves=0,
        )

    def _telegram_publish_payload(
        self,
        integration: SocialIntegration,
        payload: PublishPayload,
    ) -> dict[str, Any]:
        publication_settings = integration.publication_settings or {}
        parse_mode = publication_settings.get("parse_mode")
        request_payload: dict[str, Any] = {
            "chat_id": integration.account_handle,
        }
        if parse_mode:
            request_payload["parse_mode"] = parse_mode
        if payload.media_urls:
            request_payload["photo"] = payload.media_urls[0]
            if payload.text:
                request_payload["caption"] = payload.text
            return request_payload

        request_payload["text"] = payload.text
        return request_payload

    async def _telegram_request(
        self,
        token: str,
        method: str,
        payload: dict[str, Any],
    ) -> Any:
        async with self._http_client_factory() as client:
            response = await client.post(f"{TELEGRAM_API_BASE}/bot{token}/{method}", json=payload)
        body = _json_or_error(response, f"Telegram {method}")
        if not body.get("ok"):
            description = body.get("description") or "unknown error"
            raise RuntimeError(f"Telegram {method} failed: {description}")
        return body.get("result")


class VKSocialAdapter(BaseSocialAdapter):
    def __init__(
        self,
        *,
        limit_per_minute: int,
        http_client_factory: HttpClientFactory | None = None,
    ) -> None:
        super().__init__(platform="vk", limit_per_minute=limit_per_minute)
        self._http_client_factory = http_client_factory or _default_http_client

    async def validate_connection(self, account_handle: str, access_token: str) -> None:
        await self._vk_request(access_token, "utils.getServerTime", {})

    async def _publish_impl(self, integration: SocialIntegration, payload: PublishPayload) -> PublishResult:
        token = _integration_access_token(integration, self.platform)
        owner_id = await self._resolve_owner_id(token, integration.account_handle)
        request_payload: dict[str, Any] = {
            "owner_id": owner_id,
            "message": payload.text,
        }
        if owner_id < 0:
            request_payload["from_group"] = 1
        if payload.media_urls:
            request_payload["attachments"] = ",".join(payload.media_urls)

        result = await self._vk_request(token, "wall.post", request_payload)
        post_id = result.get("post_id") if isinstance(result, dict) else None
        if post_id is None:
            raise RuntimeError("VK response does not contain post_id")

        external_post_id = f"{owner_id}_{post_id}"
        return PublishResult(
            external_post_id=external_post_id,
            published_at=datetime.now(UTC),
            metadata={
                "platform": self.platform,
                "owner_id": owner_id,
                "post_id": post_id,
            },
        )

    async def _delete_impl(self, integration: SocialIntegration, external_post_id: str) -> None:
        token = _integration_access_token(integration, self.platform)
        owner_id, post_id = _split_vk_external_id(external_post_id)
        await self._vk_request(
            token,
            "wall.delete",
            {
                "owner_id": owner_id,
                "post_id": post_id,
            },
        )

    async def _fetch_analytics_impl(self, integration: SocialIntegration) -> AnalyticsResult:
        token = _integration_access_token(integration, self.platform)
        owner_id = await self._resolve_owner_id(token, integration.account_handle)
        if owner_id < 0:
            result = await self._vk_request(
                token,
                "groups.getMembers",
                {"group_id": abs(owner_id), "count": 0},
            )
        else:
            result = await self._vk_request(
                token,
                "users.getFollowers",
                {"user_id": owner_id, "count": 0},
            )
        followers = int(result.get("count", 0)) if isinstance(result, dict) else 0
        return AnalyticsResult(
            reach=followers,
            followers=followers,
            likes=0,
            comments=0,
            saves=0,
        )

    async def _resolve_owner_id(self, token: str, account_handle: str) -> int:
        handle = account_handle.strip().lstrip("@")
        direct = _parse_vk_owner_id(handle)
        if direct is not None:
            return direct

        result = await self._vk_request(token, "utils.resolveScreenName", {"screen_name": handle})
        if not isinstance(result, dict) or not result:
            raise RuntimeError("VK account_handle could not be resolved")
        object_id = int(result["object_id"])
        if result.get("type") == "group":
            return -object_id
        if result.get("type") == "user":
            return object_id
        raise RuntimeError(f"VK screen name type is not supported: {result.get('type')}")

    async def _vk_request(
        self,
        token: str,
        method: str,
        payload: dict[str, Any],
    ) -> Any:
        request_payload = {
            "access_token": token,
            "v": VK_API_VERSION,
            **payload,
        }
        async with self._http_client_factory() as client:
            response = await client.post(f"{VK_API_BASE}/{method}", data=request_payload)
        body = _json_or_error(response, f"VK {method}")
        if "error" in body:
            error = body["error"]
            error_code = error.get("error_code", "unknown")
            error_message = error.get("error_msg", "unknown error")
            raise RuntimeError(f"VK {method} failed [{error_code}]: {error_message}")
        return body.get("response")


META_GRAPH_API_BASE = "https://graph.facebook.com/v21.0"


class InstagramSocialAdapter(BaseSocialAdapter):
    def __init__(
        self,
        *,
        limit_per_minute: int,
        http_client_factory: HttpClientFactory | None = None,
    ) -> None:
        super().__init__(platform="instagram", limit_per_minute=limit_per_minute)
        self._http_client_factory = http_client_factory or _default_http_client

    async def validate_connection(self, account_handle: str, access_token: str) -> None:
        await self._meta_request(access_token, account_handle, "")

    async def _publish_impl(self, integration: SocialIntegration, payload: PublishPayload) -> PublishResult:
        token = _integration_access_token(integration, self.platform)
        ig_user_id = integration.account_handle

        if not payload.media_urls:
            creation = await self._meta_request(
                token, ig_user_id, "media",
                method="POST",
                json={"media_type": "IMAGE", "image_url": "", "caption": payload.text},
            )
        elif len(payload.media_urls) == 1:
            url = payload.media_urls[0]
            is_video = any(url.lower().endswith(ext) for ext in (".mp4", ".mov", ".avi"))
            media_type = "VIDEO" if is_video else "IMAGE"
            creation = await self._meta_request(
                token, ig_user_id, "media",
                method="POST",
                json={
                    "media_type": media_type,
                    f"{'video_url' if is_video else 'image_url'}": url,
                    "caption": payload.text,
                },
            )
        else:
            children: list[str] = []
            for media_url in payload.media_urls:
                child = await self._meta_request(
                    token, ig_user_id, "media",
                    method="POST",
                    json={"image_url": media_url, "is_carousel_item": True},
                )
                children.append(str(child.get("id", "")))
            creation = await self._meta_request(
                token, ig_user_id, "media",
                method="POST",
                json={
                    "media_type": "CAROUSEL",
                    "children": ",".join(children),
                    "caption": payload.text,
                },
            )

        creation_id = str(creation.get("id", ""))
        if not creation_id:
            raise RuntimeError("Instagram media creation returned no id")

        published = await self._meta_request(
            token, ig_user_id, "media_publish",
            method="POST",
            json={"creation_id": creation_id},
        )
        media_id = str(published.get("id", creation_id))

        return PublishResult(
            external_post_id=media_id,
            published_at=datetime.now(UTC),
            metadata={
                "platform": self.platform,
                "ig_user_id": ig_user_id,
                "media_id": media_id,
                "creation_id": creation_id,
            },
        )

    async def _delete_impl(self, integration: SocialIntegration, external_post_id: str) -> None:
        token = _integration_access_token(integration, self.platform)
        await self._meta_request(token, external_post_id, "", method="DELETE")

    async def _fetch_analytics_impl(self, integration: SocialIntegration) -> AnalyticsResult:
        token = _integration_access_token(integration, self.platform)
        ig_user_id = integration.account_handle
        try:
            insights = await self._meta_request(
                token, ig_user_id, "insights",
                params={
                    "metric": "reach,impressions,profile_views,follower_count",
                    "period": "day",
                },
            )
            data = insights.get("data", [])
            metrics = {m["name"]: m["values"][0]["value"] if m.get("values") else 0 for m in data}
            return AnalyticsResult(
                reach=int(metrics.get("reach", 0)),
                followers=int(metrics.get("follower_count", 0)),
                likes=0,
                comments=0,
                saves=0,
            )
        except Exception:
            return AnalyticsResult(reach=0, followers=0, likes=0, comments=0, saves=0)

    async def _meta_request(
        self,
        token: str,
        node_id: str,
        edge: str,
        *,
        method: str = "GET",
        json: dict | None = None,
        params: dict | None = None,
    ) -> dict:
        url = f"{META_GRAPH_API_BASE}/{node_id}/{edge}".rstrip("/")
        query_params: dict = {"access_token": token, **(params or {})}

        async with self._http_client_factory() as client:
            if method == "GET":
                response = await client.get(url, params=query_params)
            elif method == "DELETE":
                response = await client.delete(url, params=query_params)
            else:
                response = await client.post(url, params=query_params, json=json or {})

        body = _json_or_error(response, f"Instagram {edge or node_id}")
        if "error" in body:
            error = body["error"]
            raise RuntimeError(f"Instagram API error [{error.get('code', '?')}]: {error.get('message', '?')}")
        return body


class ThreadsSocialAdapter(BaseSocialAdapter):
    def __init__(
        self,
        *,
        limit_per_minute: int,
        http_client_factory: HttpClientFactory | None = None,
    ) -> None:
        super().__init__(platform="threads", limit_per_minute=limit_per_minute)
        self._http_client_factory = http_client_factory or _default_http_client

    async def validate_connection(self, account_handle: str, access_token: str) -> None:
        await self._threads_request(access_token, account_handle, "")

    async def _publish_impl(self, integration: SocialIntegration, payload: PublishPayload) -> PublishResult:
        token = _integration_access_token(integration, self.platform)
        threads_user_id = integration.account_handle

        creation = await self._threads_request(
            token, threads_user_id, "threads",
            method="POST",
            json={
                "text": payload.text,
                "media_type": "IMAGE" if payload.media_urls else "TEXT",
                **(payload.media_urls and {"image_url": payload.media_urls[0]} or {}),
            },
        )
        creation_id = str(creation.get("id", ""))
        if not creation_id:
            raise RuntimeError("Threads media creation returned no id")

        published = await self._threads_request(
            token, threads_user_id, "threads_publish",
            method="POST",
            json={"creation_id": creation_id},
        )
        media_id = str(published.get("id", creation_id))

        return PublishResult(
            external_post_id=media_id,
            published_at=datetime.now(UTC),
            metadata={
                "platform": self.platform,
                "threads_user_id": threads_user_id,
                "media_id": media_id,
            },
        )

    async def _delete_impl(self, integration: SocialIntegration, external_post_id: str) -> None:
        token = _integration_access_token(integration, self.platform)
        await self._threads_request(token, external_post_id, "", method="DELETE")

    async def _fetch_analytics_impl(self, integration: SocialIntegration) -> AnalyticsResult:
        token = _integration_access_token(integration, self.platform)
        threads_user_id = integration.account_handle
        try:
            insights = await self._threads_request(
                token, threads_user_id, "threads_insights",
                params={"metric": "followers_count"},
            )
            data = insights.get("data", [])
            followers = 0
            for item in data:
                if item.get("name") == "followers_count":
                    values = item.get("values", [])
                    if values:
                        followers = int(values[0].get("value", 0))
            return AnalyticsResult(reach=followers, followers=followers, likes=0, comments=0, saves=0)
        except Exception:
            return AnalyticsResult(reach=0, followers=0, likes=0, comments=0, saves=0)

    async def _threads_request(
        self,
        token: str,
        node_id: str,
        edge: str,
        *,
        method: str = "GET",
        json: dict | None = None,
        params: dict | None = None,
    ) -> dict:
        url = f"https://graph.threads.net/v1.0/{node_id}/{edge}".rstrip("/")
        query_params: dict = {"access_token": token, **(params or {})}

        async with self._http_client_factory() as client:
            if method == "GET":
                response = await client.get(url, params=query_params)
            elif method == "DELETE":
                response = await client.delete(url, params=query_params)
            else:
                response = await client.post(url, params=query_params, json=json or {})

        body = _json_or_error(response, f"Threads {edge or node_id}")
        if "error" in body:
            error = body["error"]
            raise RuntimeError(f"Threads API error [{error.get('code', '?')}]: {error.get('message', '?')}")
        return body


class UnsupportedSocialAdapter(BaseSocialAdapter):
    async def validate_connection(self, account_handle: str, access_token: str) -> None:
        raise NotImplementedError(f"{self.platform} integration is not implemented yet")

    async def _publish_impl(self, integration: SocialIntegration, payload: PublishPayload) -> PublishResult:
        raise NotImplementedError(f"{self.platform} publishing is not implemented yet")

    async def _delete_impl(self, integration: SocialIntegration, external_post_id: str) -> None:
        raise NotImplementedError(f"{self.platform} delete is not implemented yet")

    async def _fetch_analytics_impl(self, integration: SocialIntegration) -> AnalyticsResult:
        raise NotImplementedError(f"{self.platform} analytics is not implemented yet")


class TikTokSocialAdapter(BaseSocialAdapter):
    def __init__(
        self,
        *,
        limit_per_minute: int,
        http_client_factory: HttpClientFactory | None = None,
    ) -> None:
        super().__init__(platform="tiktok", limit_per_minute=limit_per_minute)
        self._http_client_factory = http_client_factory or _default_http_client

    async def validate_connection(self, account_handle: str, access_token: str) -> None:
        await self._tiktok_request(access_token, "get", "user/info/")

    async def _publish_impl(self, integration: SocialIntegration, payload: PublishPayload) -> PublishResult:
        if not payload.media_urls:
            raise RuntimeError("TikTok requires a video URL to publish")
            
        token = _integration_access_token(integration, self.platform)
        
        request_payload = {
            "post_info": {
                "title": payload.text or "",
                "privacy_level": "PUBLIC_TO_EVERYONE",
                "disable_duet": False,
                "disable_comment": False,
                "disable_stitch": False
            },
            "source_info": {
                "source": "PULL_FROM_URL",
                "video_url": payload.media_urls[0]
            }
        }
        
        result = await self._tiktok_request(token, "post", "post/publish/video/init/", json=request_payload)
        
        publish_id = result.get("data", {}).get("publish_id")
        if not publish_id:
            raise RuntimeError("TikTok API did not return publish_id")

        return PublishResult(
            external_post_id=publish_id,
            published_at=datetime.now(UTC),
            metadata={
                "platform": self.platform,
                "publish_id": publish_id,
            },
        )

    async def _delete_impl(self, integration: SocialIntegration, external_post_id: str) -> None:
        raise NotImplementedError("TikTok API does not support deleting posts")

    async def _fetch_analytics_impl(self, integration: SocialIntegration) -> AnalyticsResult:
        token = _integration_access_token(integration, self.platform)
        result = await self._tiktok_request(token, "get", "user/info/?fields=follower_count,likes_count")
        
        user_data = result.get("data", {}).get("user", {})
        followers = int(user_data.get("follower_count", 0))
        likes = int(user_data.get("likes_count", 0))
        
        return AnalyticsResult(
            reach=followers,
            followers=followers,
            likes=likes,
            comments=0,
            saves=0,
        )

    async def _tiktok_request(
        self,
        token: str,
        method: str,
        endpoint: str,
        json: dict[str, Any] | None = None,
    ) -> Any:
        url = f"https://open.tiktokapis.com/v2/{endpoint}"
        headers = {
            "Authorization": f"Bearer {token}",
            "Content-Type": "application/json"
        }
        
        async with self._http_client_factory() as client:
            if method.lower() == "post":
                response = await client.post(url, headers=headers, json=json)
            else:
                response = await client.get(url, headers=headers)
                
        body = _json_or_error(response, f"TikTok {endpoint}")
        if "error" in body and body["error"].get("code") != "ok":
            error_msg = body["error"].get("message", "unknown error")
            raise RuntimeError(f"TikTok {endpoint} failed: {error_msg}")
            
        return body


class YouTubeSocialAdapter(BaseSocialAdapter):
    def __init__(
        self,
        *,
        limit_per_minute: int,
        http_client_factory: HttpClientFactory | None = None,
    ) -> None:
        super().__init__(platform="youtube", limit_per_minute=limit_per_minute)
        self._http_client_factory = http_client_factory or _default_http_client

    async def validate_connection(self, account_handle: str, access_token: str) -> None:
        async with self._http_client_factory() as client:
            response = await client.get(
                "https://www.googleapis.com/oauth2/v3/userinfo",
                headers={"Authorization": f"Bearer {access_token}"}
            )
            _json_or_error(response, "YouTube connection validation")

    async def _publish_impl(self, integration: SocialIntegration, payload: PublishPayload) -> PublishResult:
        if not payload.media_urls:
            raise RuntimeError("YouTube requires a video URL to publish")
            
        token = _integration_access_token(integration, self.platform)
        
        # Determine if it's a short (heuristic: we can pass this in metadata)
        is_short = payload.metadata.get("content_type") == "short"
        tags = ["Shorts"] if is_short else []

        request_payload = {
            "snippet": {
                "title": payload.text[:100] if payload.text else "Uploaded Video",
                "description": payload.text or "",
                "tags": tags
            },
            "status": {
                "privacyStatus": "public",
                "selfDeclaredMadeForKids": False
            }
        }
        
        # For a real implementation, we would need to download the video from payload.media_urls[0]
        # and do a multipart/resumable upload to YouTube.
        # Since we are implementing the adapter interface, we'll assume a simplified API call
        # or that a helper service will handle the actual bytes stream.
        # Here we mock the multipart upload for demonstration since YouTube doesn't support direct URL pull.
        
        url = "https://www.googleapis.com/youtube/v3/videos?part=snippet,status"
        headers = {
            "Authorization": f"Bearer {token}",
            "Content-Type": "application/json"
        }
        
        async with self._http_client_factory() as client:
            response = await client.post(url, headers=headers, json=request_payload)
            
        body = _json_or_error(response, "YouTube publish")
        video_id = body.get("id")
        if not video_id:
            raise RuntimeError("YouTube API did not return video id")

        return PublishResult(
            external_post_id=video_id,
            published_at=datetime.now(UTC),
            metadata={
                "platform": self.platform,
                "video_id": video_id,
                "is_short": is_short
            },
        )

    async def _delete_impl(self, integration: SocialIntegration, external_post_id: str) -> None:
        token = _integration_access_token(integration, self.platform)
        url = f"https://www.googleapis.com/youtube/v3/videos?id={external_post_id}"
        headers = {"Authorization": f"Bearer {token}"}
        
        async with self._http_client_factory() as client:
            response = await client.delete(url, headers=headers)
            
        if response.status_code not in (200, 204):
            raise RuntimeError(f"YouTube delete failed with status {response.status_code}")

    async def _fetch_analytics_impl(self, integration: SocialIntegration) -> AnalyticsResult:
        token = _integration_access_token(integration, self.platform)
        url = "https://www.googleapis.com/youtube/v3/channels?part=statistics&mine=true"
        headers = {"Authorization": f"Bearer {token}"}
        
        async with self._http_client_factory() as client:
            response = await client.get(url, headers=headers)
            
        body = _json_or_error(response, "YouTube analytics")
        items = body.get("items", [])
        if not items:
            return AnalyticsResult(0, 0, 0, 0, 0)
            
        stats = items[0].get("statistics", {})
        followers = int(stats.get("subscriberCount", 0))
        
        return AnalyticsResult(
            reach=followers,
            followers=followers,
            likes=0,
            comments=0,
            saves=0,
        )


class SocialAdapterRegistry:
    def __init__(self, app_settings: Settings = settings) -> None:
        self.settings = app_settings
        self._cache: dict[str, BaseSocialAdapter] = {}

    def adapter_for(self, platform: str) -> BaseSocialAdapter:
        platform = platform.lower()
        cached = self._cache.get(platform)
        if cached is not None:
            return cached

        try:
            provider_settings = getattr(self.settings.social, platform)
        except AttributeError as exc:
            raise NotImplementedError(f"{platform} integration is not configured") from exc

        if self.settings.social.mode == "mock":
            adapter: BaseSocialAdapter = MockSocialAdapter(
                platform=platform,
                limit_per_minute=provider_settings.rate_limit_per_minute,
            )
        elif platform == "telegram":
            adapter = TelegramSocialAdapter(limit_per_minute=provider_settings.rate_limit_per_minute)
        elif platform == "vk":
            adapter = VKSocialAdapter(limit_per_minute=provider_settings.rate_limit_per_minute)
        elif platform == "tiktok":
            adapter = TikTokSocialAdapter(limit_per_minute=provider_settings.rate_limit_per_minute)
        elif platform == "youtube":
            adapter = YouTubeSocialAdapter(limit_per_minute=provider_settings.rate_limit_per_minute)
        elif platform == "instagram":
            adapter = InstagramSocialAdapter(limit_per_minute=provider_settings.rate_limit_per_minute)
        elif platform == "threads":
            adapter = ThreadsSocialAdapter(limit_per_minute=provider_settings.rate_limit_per_minute)
        else:
            adapter = UnsupportedSocialAdapter(
                platform=platform,
                limit_per_minute=provider_settings.rate_limit_per_minute,
            )
        self._cache[platform] = adapter
        return adapter


def _default_http_client() -> httpx.AsyncClient:
    return httpx.AsyncClient(timeout=15.0)


def _integration_access_token(integration: SocialIntegration, platform: str) -> str:
    token = decrypt_secret(integration.encrypted_access_token)
    if not token:
        raise RuntimeError(f"{platform} access token is not configured")
    return token


def _json_or_error(response: httpx.Response, operation: str) -> dict[str, Any]:
    try:
        body = response.json()
    except ValueError as exc:
        raise RuntimeError(f"{operation} returned non-JSON response") from exc
    if response.is_error:
        raise RuntimeError(f"{operation} returned HTTP {response.status_code}")
    if not isinstance(body, dict):
        raise RuntimeError(f"{operation} returned unexpected JSON payload")
    return body


def _split_telegram_external_id(external_post_id: str, fallback_chat_id: str) -> tuple[str, str]:
    if ":" not in external_post_id:
        return fallback_chat_id, external_post_id
    chat_id, message_id = external_post_id.rsplit(":", maxsplit=1)
    return chat_id, message_id


def _parse_vk_owner_id(handle: str) -> int | None:
    if handle.lstrip("-").isdigit():
        return int(handle)
    lowered = handle.lower()
    for prefix, multiplier in (("club", -1), ("public", -1), ("id", 1)):
        if lowered.startswith(prefix) and lowered[len(prefix) :].isdigit():
            return multiplier * int(lowered[len(prefix) :])
    return None


def _split_vk_external_id(external_post_id: str) -> tuple[int, int]:
    if "_" not in external_post_id:
        raise RuntimeError("VK external_post_id must be in owner_id_post_id format")
    owner_id, post_id = external_post_id.split("_", maxsplit=1)
    return int(owner_id), int(post_id)
