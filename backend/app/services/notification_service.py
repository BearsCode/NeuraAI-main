from __future__ import annotations

from collections.abc import Sequence

import httpx
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from backend.app.core.configs import settings
from backend.app.db.notification import Notification
from backend.app.db.tenant_membership import TenantMembership


class NotificationService:
    """Send admin alerts and persist in-app notifications."""

    async def notify_publication_failure(
        self,
        session: AsyncSession,
        *,
        tenant_id: str,
        project_id: str,
        title: str,
        message: str,
        metadata: dict,
        alert_telegram_admins: bool = False,
    ) -> None:
        """Create tenant user notifications and optionally alert Telegram admins."""

        user_ids = await session.scalars(
            select(TenantMembership.user_id).where(TenantMembership.tenant_id == tenant_id)
        )
        for user_id in user_ids:
            session.add(
                Notification(
                    tenant_id=tenant_id,
                    user_id=user_id,
                    project_id=project_id,
                    channel="in_app",
                    severity="error",
                    title=title,
                    message=message,
                    metadata_json=metadata,
                )
            )

        if alert_telegram_admins:
            try:
                await self._send_telegram_admin_alert(title=title, message=message, metadata=metadata)
            except Exception:
                return

    async def _send_telegram_admin_alert(
        self,
        *,
        title: str,
        message: str,
        metadata: dict,
    ) -> None:
        token = settings.telegram.bot_token.get_secret_value() if settings.telegram.bot_token else None
        admin_ids: Sequence[int] = settings.telegram.admin_ids
        if not token or not admin_ids:
            return

        text = (
            f"<b>{title}</b>\n"
            f"{message}\n"
            f"<code>{metadata}</code>"
        )
        async with httpx.AsyncClient(timeout=10.0) as client:
            for admin_id in admin_ids:
                await client.post(
                    f"https://api.telegram.org/bot{token}/sendMessage",
                    json={
                        "chat_id": admin_id,
                        "text": text,
                        "parse_mode": "HTML",
                    },
                )
