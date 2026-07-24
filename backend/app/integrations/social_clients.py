from __future__ import annotations

import base64
import hashlib
import secrets
from abc import ABC, abstractmethod
from collections.abc import Callable
from dataclasses import dataclass
from datetime import UTC, datetime, timedelta
from typing import Any
from urllib.parse import urlencode

import httpx

from backend.app.core.configs import settings
from backend.app.core.security import decrypt_secret
from backend.app.db.social_integration import SocialIntegration
from backend.app.integrations.social_adapters import PublishPayload, PublishResult, SocialAdapterRegistry

VK_OAUTH_AUTHORIZE_URL = "https://oauth.vk.com/authorize"
VK_OAUTH_TOKEN_URL = "https://oauth.vk.com/access_token"
TIKTOK_OAUTH_AUTHORIZE_URL = "https://www.tiktok.com/v2/auth/authorize/"
TIKTOK_OAUTH_TOKEN_URL = "https://open.tiktokapis.com/v2/oauth/token/"
YOUTUBE_OAUTH_AUTHORIZE_URL = "https://accounts.google.com/o/oauth2/v2/auth"
YOUTUBE_OAUTH_TOKEN_URL = "https://oauth2.googleapis.com/token"
HTTP_LIMITS = httpx.Limits(max_connections=20, max_keepalive_connections=10)


@dataclass(slots=True)
class SocialAuthStart:
    """Authorization URL and transient PKCE data."""

    authorization_url: str
    state: str
    code_verifier: str | None = None


@dataclass(slots=True)
class SocialAccount:
    """External social account available for connection."""

    account_handle: str
    title: str
    metadata: dict[str, Any]


@dataclass(slots=True)
class SocialAuthResult:
    """Tokens and account metadata returned from a social auth callback."""

    access_token: str
    refresh_token: str | None
    expires_at: datetime | None
    account_handle: str
    scopes: list[str]
    accounts: list[SocialAccount]
    metadata: dict[str, Any]


class BaseSocialClient(ABC):
    """Provider-facing client used for auth flows and outbound posting."""

    def __init__(
        self,
        platform: str,
        http_client_factory: Callable[[], httpx.AsyncClient] | None = None,
    ) -> None:
        self.platform = platform
        self._http_client_factory = http_client_factory or self._default_http_client

    @abstractmethod
    async def auth(self, redirect_uri: str) -> SocialAuthStart:
        """Build a provider-specific authorization URL."""

    @abstractmethod
    async def callback(
        self,
        code: str,
        redirect_uri: str,
        *,
        code_verifier: str | None = None,
        account_hint: str | None = None,
    ) -> SocialAuthResult:
        """Exchange a provider callback code into durable credentials."""

    async def post_message(
        self,
        integration: SocialIntegration,
        text: str,
        media_urls: list[str] | None = None,
    ) -> PublishResult:
        """Publish a message through the existing adapter layer."""

        adapter = SocialAdapterRegistry().adapter_for(self.platform)
        return await adapter.publish(
            integration,
            PublishPayload(
                text=text,
                media_urls=media_urls or [],
                scheduled_at=None,
                metadata={"source": "social_client"},
            ),
        )

    def _default_http_client(self) -> httpx.AsyncClient:
        return httpx.AsyncClient(timeout=20.0, limits=HTTP_LIMITS)

    def _http_client(self) -> httpx.AsyncClient:
        return self._http_client_factory()


class VKSocialClient(BaseSocialClient):
    """VK OAuth 2.x client."""

    def __init__(self, http_client_factory: Callable[[], httpx.AsyncClient] | None = None) -> None:
        super().__init__(platform="vk", http_client_factory=http_client_factory)

    async def auth(self, redirect_uri: str) -> SocialAuthStart:
        provider = settings.social.vk
        if not provider.oauth_configured or not provider.client_id:
            raise RuntimeError("VK OAuth client_id/client_secret are not configured")

        state = secrets.token_urlsafe(24)
        code_verifier = secrets.token_urlsafe(48)
        code_challenge = base64.urlsafe_b64encode(
            hashlib.sha256(code_verifier.encode("utf-8")).digest()
        ).rstrip(b"=").decode("utf-8")
        query = urlencode(
            {
                "client_id": provider.client_id,
                "redirect_uri": redirect_uri,
                "response_type": "code",
                "scope": "wall,groups,offline",
                "state": state,
                "code_challenge": code_challenge,
                "code_challenge_method": "S256",
                "v": "5.199",
            }
        )
        return SocialAuthStart(
            authorization_url=f"{VK_OAUTH_AUTHORIZE_URL}?{query}",
            state=state,
            code_verifier=code_verifier,
        )

    async def callback(
        self,
        code: str,
        redirect_uri: str,
        *,
        code_verifier: str | None = None,
        account_hint: str | None = None,
    ) -> SocialAuthResult:
        provider = settings.social.vk
        if not provider.client_id or not provider.client_secret:
            raise RuntimeError("VK OAuth client is not configured")

        payload: dict[str, Any] = {
            "client_id": provider.client_id,
            "client_secret": provider.client_secret.get_secret_value(),
            "redirect_uri": redirect_uri,
            "code": code,
        }
        if code_verifier:
            payload["code_verifier"] = code_verifier

        async with self._http_client() as client:
            token_response = await client.get(VK_OAUTH_TOKEN_URL, params=payload)
            token_response.raise_for_status()
            token_data = token_response.json()
            if "error" in token_data:
                raise RuntimeError(f"VK token exchange failed: {token_data['error']}")

            access_token = str(token_data["access_token"])
            user_id = token_data.get("user_id")
            expires_in = int(token_data.get("expires_in", 0) or 0)
            expires_at = datetime.now(UTC) + timedelta(seconds=expires_in) if expires_in else None
            pages = await self._load_admin_groups(client, access_token, user_id)

        selected_account = account_hint or (pages[0].account_handle if pages else (f"id{user_id}" if user_id else ""))
        scopes = ["wall", "groups", "offline"]
        return SocialAuthResult(
            access_token=access_token,
            refresh_token=None,
            expires_at=expires_at,
            account_handle=selected_account,
            scopes=scopes,
            accounts=pages,
            metadata={"user_id": user_id},
        )

    async def _load_admin_groups(
        self,
        client: httpx.AsyncClient,
        access_token: str,
        user_id: int | None,
    ) -> list[SocialAccount]:
        params = {
            "access_token": access_token,
            "extended": 1,
            "filter": "admin,editor,moder",
            "v": "5.199",
        }
        response = await client.get("https://api.vk.com/method/groups.get", params=params)
        response.raise_for_status()
        payload = response.json()
        raw_items = payload.get("response", {}).get("items", [])
        accounts = [
            SocialAccount(
                account_handle=f"club{item['id']}",
                title=item.get("name", f"VK group {item['id']}"),
                metadata={"group_id": item["id"], "screen_name": item.get("screen_name")},
            )
            for item in raw_items
        ]
        if not accounts and user_id:
            accounts.append(
                SocialAccount(
                    account_handle=f"id{user_id}",
                    title=f"VK user {user_id}",
                    metadata={"user_id": user_id},
                )
            )
        return accounts


class TelegramSocialClient(BaseSocialClient):
    """Telegram Bot API onboarding client."""

    def __init__(self, http_client_factory: Callable[[], httpx.AsyncClient] | None = None) -> None:
        super().__init__(platform="telegram", http_client_factory=http_client_factory)

    async def auth(self, redirect_uri: str) -> SocialAuthStart:
        bot_token = settings.telegram.bot_token.get_secret_value() if settings.telegram.bot_token else None
        bot_name = "BotFather"
        if bot_token:
            bot_name = f"bot{bot_token.split(':', maxsplit=1)[0]}"
        return SocialAuthStart(
            authorization_url=f"https://t.me/{bot_name}",
            state=secrets.token_urlsafe(24),
            code_verifier=None,
        )

    async def callback(
        self,
        code: str,
        redirect_uri: str,
        *,
        code_verifier: str | None = None,
        account_hint: str | None = None,
    ) -> SocialAuthResult:
        del redirect_uri, code_verifier
        if not account_hint:
            raise RuntimeError("Telegram callback requires channel/account handle as account_hint")

        token = code.strip()
        async with self._http_client() as client:
            me_response = await client.post(f"https://api.telegram.org/bot{token}/getMe")
            me_response.raise_for_status()
            me_payload = me_response.json()
            if not me_payload.get("ok"):
                raise RuntimeError("Telegram bot token validation failed")

            chat_response = await client.post(
                f"https://api.telegram.org/bot{token}/getChat",
                json={"chat_id": account_hint},
            )
            chat_response.raise_for_status()
            chat_payload = chat_response.json()
            if not chat_payload.get("ok"):
                raise RuntimeError("Telegram channel handle validation failed")

        bot_info = me_payload["result"]
        channel_info = chat_payload["result"]
        return SocialAuthResult(
            access_token=token,
            refresh_token=None,
            expires_at=None,
            account_handle=account_hint,
            scopes=["messages", "media"],
            accounts=[
                SocialAccount(
                    account_handle=account_hint,
                    title=channel_info.get("title", account_hint),
                    metadata={"chat_id": channel_info.get("id"), "type": channel_info.get("type")},
                )
            ],
            metadata={"bot_username": bot_info.get("username")},
        )



class TikTokSocialClient(BaseSocialClient):
    """TikTok OAuth 2.x client."""

    def __init__(self, http_client_factory: Callable[[], httpx.AsyncClient] | None = None) -> None:
        super().__init__(platform="tiktok", http_client_factory=http_client_factory)

    async def auth(self, redirect_uri: str) -> SocialAuthStart:
        provider = settings.social.tiktok
        if not provider.oauth_configured or not provider.client_id:
            raise RuntimeError("TikTok OAuth client_id/client_secret are not configured")

        state = secrets.token_urlsafe(24)
        code_verifier = secrets.token_urlsafe(48)
        query = urlencode(
            {
                "client_key": provider.client_id,
                "response_type": "code",
                "scope": "user.info.basic,video.upload,video.publish",
                "redirect_uri": redirect_uri,
                "state": state,
            }
        )
        return SocialAuthStart(
            authorization_url=f"{TIKTOK_OAUTH_AUTHORIZE_URL}?{query}",
            state=state,
            code_verifier=code_verifier,
        )

    async def callback(
        self,
        code: str,
        redirect_uri: str,
        *,
        code_verifier: str | None = None,
        account_hint: str | None = None,
    ) -> SocialAuthResult:
        provider = settings.social.tiktok
        if not provider.client_id or not provider.client_secret:
            raise RuntimeError("TikTok OAuth client is not configured")

        payload: dict[str, Any] = {
            "client_key": provider.client_id,
            "client_secret": provider.client_secret.get_secret_value(),
            "code": code,
            "grant_type": "authorization_code",
            "redirect_uri": redirect_uri,
        }

        async with self._http_client() as client:
            headers = {"Content-Type": "application/x-www-form-urlencoded", "Cache-Control": "no-cache"}
            token_response = await client.post(TIKTOK_OAUTH_TOKEN_URL, data=payload, headers=headers)
            token_response.raise_for_status()
            token_data = token_response.json()
            if "error" in token_data:
                raise RuntimeError(f"TikTok token exchange failed: {token_data['error']}")

            access_token = str(token_data["access_token"])
            refresh_token = str(token_data.get("refresh_token", ""))
            open_id = str(token_data.get("open_id", ""))
            scopes = token_data.get("scope", "").split(",")
            expires_in = int(token_data.get("expires_in", 0) or 0)
            expires_at = datetime.now(UTC) + timedelta(seconds=expires_in) if expires_in else None

            # Get user info
            user_response = await client.get(
                "https://open.tiktokapis.com/v2/user/info/?fields=display_name,avatar_url",
                headers={"Authorization": f"Bearer {access_token}"}
            )
            user_response.raise_for_status()
            user_data = user_response.json()
            display_name = user_data.get("data", {}).get("user", {}).get("display_name", f"tiktok_{open_id}")

        selected_account = account_hint or open_id
        return SocialAuthResult(
            access_token=access_token,
            refresh_token=refresh_token or None,
            expires_at=expires_at,
            account_handle=selected_account,
            scopes=scopes,
            accounts=[
                SocialAccount(
                    account_handle=open_id,
                    title=display_name,
                    metadata={"open_id": open_id},
                )
            ],
            metadata={"open_id": open_id, "display_name": display_name},
        )


class YouTubeSocialClient(BaseSocialClient):
    """YouTube (Google) OAuth 2.0 client."""

    def __init__(self, http_client_factory: Callable[[], httpx.AsyncClient] | None = None) -> None:
        super().__init__(platform="youtube", http_client_factory=http_client_factory)

    async def auth(self, redirect_uri: str) -> SocialAuthStart:
        provider = settings.social.youtube
        if not provider.oauth_configured or not provider.client_id:
            raise RuntimeError("YouTube OAuth client_id/client_secret are not configured")

        state = secrets.token_urlsafe(24)
        query = urlencode(
            {
                "client_id": provider.client_id,
                "response_type": "code",
                "scope": "https://www.googleapis.com/auth/youtube.upload https://www.googleapis.com/auth/userinfo.profile",
                "redirect_uri": redirect_uri,
                "state": state,
                "access_type": "offline",
                "prompt": "consent",
            }
        )
        return SocialAuthStart(
            authorization_url=f"{YOUTUBE_OAUTH_AUTHORIZE_URL}?{query}",
            state=state,
            code_verifier=None,
        )

    async def callback(
        self,
        code: str,
        redirect_uri: str,
        *,
        code_verifier: str | None = None,
        account_hint: str | None = None,
    ) -> SocialAuthResult:
        provider = settings.social.youtube
        if not provider.client_id or not provider.client_secret:
            raise RuntimeError("YouTube OAuth client is not configured")

        payload: dict[str, Any] = {
            "client_id": provider.client_id,
            "client_secret": provider.client_secret.get_secret_value(),
            "code": code,
            "grant_type": "authorization_code",
            "redirect_uri": redirect_uri,
        }

        async with self._http_client() as client:
            token_response = await client.post(YOUTUBE_OAUTH_TOKEN_URL, data=payload)
            token_response.raise_for_status()
            token_data = token_response.json()
            if "error" in token_data:
                raise RuntimeError(f"YouTube token exchange failed: {token_data['error']}")

            access_token = str(token_data["access_token"])
            refresh_token = str(token_data.get("refresh_token", ""))
            scopes = token_data.get("scope", "").split(" ")
            expires_in = int(token_data.get("expires_in", 0) or 0)
            expires_at = datetime.now(UTC) + timedelta(seconds=expires_in) if expires_in else None

            # Fetch user profile to get Google ID and Name
            user_response = await client.get(
                "https://www.googleapis.com/oauth2/v3/userinfo",
                headers={"Authorization": f"Bearer {access_token}"}
            )
            user_response.raise_for_status()
            user_data = user_response.json()
            
            google_id = user_data.get("sub", "")
            display_name = user_data.get("name", f"youtube_{google_id}")

        selected_account = account_hint or google_id
        return SocialAuthResult(
            access_token=access_token,
            refresh_token=refresh_token or None,
            expires_at=expires_at,
            account_handle=selected_account,
            scopes=scopes,
            accounts=[
                SocialAccount(
                    account_handle=google_id,
                    title=display_name,
                    metadata={"google_id": google_id},
                )
            ],
            metadata={"google_id": google_id, "display_name": display_name},
        )


class InstagramSocialClient(BaseSocialClient):
    """Meta Graph API OAuth client for Instagram Business/Creator accounts."""

    META_OAUTH_AUTHORIZE_URL = "https://www.facebook.com/v21.0/dialog/oauth"
    META_OAUTH_TOKEN_URL = "https://graph.facebook.com/v21.0/oauth/access_token"

    def __init__(self, http_client_factory: Callable[[], httpx.AsyncClient] | None = None) -> None:
        super().__init__(platform="instagram", http_client_factory=http_client_factory)

    async def auth(self, redirect_uri: str) -> SocialAuthStart:
        provider = settings.social.instagram
        if not provider.oauth_configured or not provider.client_id:
            raise RuntimeError("Instagram OAuth client_id/client_secret are not configured")

        state = secrets.token_urlsafe(24)
        query = urlencode({
            "client_id": provider.client_id,
            "redirect_uri": redirect_uri,
            "state": state,
            "scope": "instagram_basic,instagram_content_publish,pages_read_engagement,pages_show_list",
            "response_type": "code",
        })
        return SocialAuthStart(
            authorization_url=f"{self.META_OAUTH_AUTHORIZE_URL}?{query}",
            state=state,
        )

    async def callback(
        self,
        code: str,
        redirect_uri: str,
        *,
        code_verifier: str | None = None,
        account_hint: str | None = None,
    ) -> SocialAuthResult:
        provider = settings.social.instagram
        if not provider.client_id or not provider.client_secret:
            raise RuntimeError("Instagram OAuth client is not configured")

        async with self._http_client() as client:
            token_response = await client.get(
                self.META_OAUTH_TOKEN_URL,
                params={
                    "client_id": provider.client_id,
                    "client_secret": provider.client_secret.get_secret_value(),
                    "redirect_uri": redirect_uri,
                    "code": code,
                },
            )
            token_response.raise_for_status()
            token_data = token_response.json()
            if "error" in token_data:
                raise RuntimeError(f"Instagram token exchange failed: {token_data['error']}")

            access_token = str(token_data.get("access_token", ""))
            if not access_token:
                raise RuntimeError("Instagram token exchange returned no access_token")

            pages = await client.get(
                "https://graph.facebook.com/v21.0/me/accounts",
                params={"access_token": access_token},
            )
            pages.raise_for_status()
            pages_data = pages.json()

            accounts: list[SocialAccount] = []
            for page in pages_data.get("data", []):
                page_id = page.get("id", "")
                page_name = page.get("name", "")
                page_token = page.get("access_token", "")

                ig_response = await client.get(
                    f"https://graph.facebook.com/v21.0/{page_id}",
                    params={
                        "access_token": page_token,
                        "fields": "instagram_business_account{id,username,name}",
                    },
                )
                ig_data = ig_response.json()
                ig_business = ig_data.get("instagram_business_account")
                if ig_business:
                    accounts.append(SocialAccount(
                        account_handle=str(ig_business["id"]),
                        title=ig_business.get("name", ig_business.get("username", page_name)),
                        metadata={"page_id": page_id, "page_name": page_name, "ig_username": ig_business.get("username", "")},
                    ))

            if not accounts:
                raise RuntimeError("No Instagram Business Accounts found. Connect your Page to an Instagram Business account.")

            selected = account_hint or accounts[0].account_handle
            return SocialAuthResult(
                access_token=access_token,
                refresh_token=None,
                expires_at=None,
                account_handle=selected,
                scopes=["instagram_basic", "instagram_content_publish"],
                accounts=accounts,
                metadata={"token_type": "instagram_page_token"},
            )


class ThreadsSocialClient(BaseSocialClient):
    """Meta Graph API OAuth client for Threads accounts."""

    META_OAUTH_AUTHORIZE_URL = "https://www.facebook.com/v21.0/dialog/oauth"
    META_OAUTH_TOKEN_URL = "https://graph.facebook.com/v21.0/oauth/access_token"

    def __init__(self, http_client_factory: Callable[[], httpx.AsyncClient] | None = None) -> None:
        super().__init__(platform="threads", http_client_factory=http_client_factory)

    async def auth(self, redirect_uri: str) -> SocialAuthStart:
        provider = settings.social.threads
        if not provider.oauth_configured or not provider.client_id:
            raise RuntimeError("Threads OAuth client_id/client_secret are not configured")

        state = secrets.token_urlsafe(24)
        query = urlencode({
            "client_id": provider.client_id,
            "redirect_uri": redirect_uri,
            "state": state,
            "scope": "threads_basic,threads_content_publish,threads_manage_insights",
            "response_type": "code",
        })
        return SocialAuthStart(
            authorization_url=f"{self.META_OAUTH_AUTHORIZE_URL}?{query}",
            state=state,
        )

    async def callback(
        self,
        code: str,
        redirect_uri: str,
        *,
        code_verifier: str | None = None,
        account_hint: str | None = None,
    ) -> SocialAuthResult:
        provider = settings.social.threads
        if not provider.client_id or not provider.client_secret:
            raise RuntimeError("Threads OAuth client is not configured")

        async with self._http_client() as client:
            token_response = await client.get(
                self.META_OAUTH_TOKEN_URL,
                params={
                    "client_id": provider.client_id,
                    "client_secret": provider.client_secret.get_secret_value(),
                    "redirect_uri": redirect_uri,
                    "code": code,
                },
            )
            token_response.raise_for_status()
            token_data = token_response.json()
            if "error" in token_data:
                raise RuntimeError(f"Threads token exchange failed: {token_data['error']}")

            access_token = str(token_data.get("access_token", ""))
            if not access_token:
                raise RuntimeError("Threads token exchange returned no access_token")

            me_response = await client.get(
                "https://graph.threads.net/v21.0/me",
                params={"access_token": access_token, "fields": "id,username,name"},
            )
            me_response.raise_for_status()
            me_data = me_response.json()

            threads_user_id = str(me_data.get("id", ""))
            threads_username = me_data.get("username", account_hint or "")
            threads_name = me_data.get("name", threads_username)

            accounts = [
                SocialAccount(
                    account_handle=threads_user_id,
                    title=threads_name,
                    metadata={"username": threads_username},
                )
            ]
            return SocialAuthResult(
                access_token=access_token,
                refresh_token=None,
                expires_at=None,
                account_handle=threads_user_id,
                scopes=["threads_basic", "threads_content_publish", "threads_manage_insights"],
                accounts=accounts,
                metadata={"username": threads_username},
            )



class SocialClientRegistry:
    """Resolve a provider-specific social client."""

    def client_for(self, platform: str) -> BaseSocialClient:
        normalized = platform.lower()
        if normalized == "vk":
            return VKSocialClient()
        if normalized == "telegram":
            return TelegramSocialClient()
        if normalized == "tiktok":
            return TikTokSocialClient()
        if normalized == "youtube":
            return YouTubeSocialClient()
        if normalized == "instagram":
            return InstagramSocialClient()
        if normalized == "threads":
            return ThreadsSocialClient()
        raise NotImplementedError(f"{platform} social client is not implemented")


def integration_access_token(integration: SocialIntegration) -> str:
    """Expose decrypted access token for provider-specific flows."""

    token = decrypt_secret(integration.encrypted_access_token)
    if not token:
        raise RuntimeError(f"{integration.platform.value} access token is not configured")
    return token
