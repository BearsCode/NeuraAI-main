from __future__ import annotations

from datetime import UTC, datetime, timedelta

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from backend.app.db.enums import SubscriptionStatus
from backend.app.db.subscription import Subscription
from backend.app.db.tenant import Tenant
from backend.app.db.user import User
from backend.app.observability.logging import get_logger
from backend.app.services.email_service import email_service

logger = get_logger(__name__)

DUNNING_DELAYS_DAYS = [1, 3, 7, 14]
GRACE_PERIOD_DAYS = 30


class SubscriptionLifecycleService:
    async def _owner_email(self, session: AsyncSession, tenant_id: str) -> str | None:
        tenant = await session.get(Tenant, tenant_id)
        if tenant is None:
            return None
        user = await session.get(User, tenant.owner_user_id)
        return user.email if user else None

    async def process_expired_trials(self, session: AsyncSession) -> list[str]:
        now = datetime.now(UTC)
        expired = await session.scalars(
            select(Subscription)
            .where(
                Subscription.status == SubscriptionStatus.TRIAL,
                Subscription.trial_ends_at.isnot(None),
                Subscription.trial_ends_at <= now,
            )
        )
        ids: list[str] = []
        for sub in expired.all():
            sub.status = SubscriptionStatus.PAST_DUE
            sub.next_charge_at = now + timedelta(days=GRACE_PERIOD_DAYS)
            session.add(sub)
            ids.append(sub.id)
            logger.info("trial_expired", subscription_id=sub.id, tenant_id=sub.tenant_id)

            email = await self._owner_email(session, sub.tenant_id)
            if email:
                await email_service.send_email(
                    to=email,
                    subject="Пробный период закончился — NeuaraAI",
                    html_body=(
                        "<h2>Пробный период закончился</h2>"
                        "<p>Ваш пробный доступ к NeuaraAI завершён.</p>"
                        "<p>Чтобы продолжить пользоваться платформой, выберите тариф и оплатите подписку.</p>"
                        "<p>У вас есть 30 дней, чтобы возобновить подписку без потери данных.</p>"
                    ),
                )
        if ids:
            await session.commit()
        return ids

    async def process_past_due(self, session: AsyncSession) -> list[str]:
        now = datetime.now(UTC)
        past_due = await session.scalars(
            select(Subscription)
            .options(selectinload(Subscription.payments))
            .where(
                Subscription.status == SubscriptionStatus.PAST_DUE,
                Subscription.next_charge_at.isnot(None),
                Subscription.next_charge_at <= now,
            )
        )
        ids: list[str] = []
        for sub in past_due.all():
            grace_end = sub.next_charge_at + timedelta(days=GRACE_PERIOD_DAYS)
            if now >= grace_end:
                sub.status = SubscriptionStatus.EXPIRED
                logger.info("subscription_expired", subscription_id=sub.id, tenant_id=sub.tenant_id)
                email = await self._owner_email(session, sub.tenant_id)
                if email:
                    await email_service.send_email(
                        to=email,
                        subject="Подписка отключена — NeuaraAI",
                        html_body=(
                            "<h2>Подписка отключена</h2>"
                            "<p>Ваша подписка NeuaraAI отключена из-за отсутствия оплаты.</p>"
                            "<p>Все данные сохранены. Для восстановления доступа свяжитесь с поддержкой.</p>"
                        ),
                    )
            else:
                dunning_day = (now - sub.next_charge_at).days
                logger.info(
                    "subscription_past_due_dunning",
                    subscription_id=sub.id,
                    tenant_id=sub.tenant_id,
                    days_overdue=dunning_day,
                )
                email = await self._owner_email(session, sub.tenant_id)
                if email:
                    await email_service.send_email(
                        to=email,
                        subject=f"Просрочка оплаты — NeuaraAI (день {dunning_day})",
                        html_body=(
                            f"<h2>Просрочка оплаты: {dunning_day} дн.</h2>"
                            "<p>Оплата подписки NeuaraAI просрочена.</p>"
                            f"<p>Подписка будет отключена через {GRACE_PERIOD_DAYS - dunning_day} дн.</p>"
                            "<p>Пожалуйста, оплатите подписку в личном кабинете.</p>"
                        ),
                    )
            session.add(sub)
            ids.append(sub.id)
        if ids:
            await session.commit()
        return ids

    async def process_pending_payment_timeout(self, session: AsyncSession) -> list[str]:
        now = datetime.now(UTC)
        stale = await session.scalars(
            select(Subscription)
            .where(
                Subscription.status == SubscriptionStatus.PENDING_PAYMENT,
                Subscription.updated_at.isnot(None),
                Subscription.updated_at <= now - timedelta(hours=1),
            )
        )
        ids: list[str] = []
        for sub in stale.all():
            sub.status = SubscriptionStatus.PAST_DUE
            session.add(sub)
            ids.append(sub.id)
            logger.info("pending_payment_timeout", subscription_id=sub.id, tenant_id=sub.tenant_id)

            email = await self._owner_email(session, sub.tenant_id)
            if email:
                await email_service.send_email(
                    to=email,
                    subject="Платёж не завершён — NeuaraAI",
                    html_body=(
                        "<h2>Платёж не завершён</h2>"
                        "<p>Мы не получили подтверждение оплаты. Попробуйте ещё раз.</p>"
                        "<p>Если проблема повторится, обратитесь в поддержку.</p>"
                    ),
                )
        if ids:
            await session.commit()
        return ids

    async def run_all(self, session: AsyncSession) -> dict[str, int]:
        expired_trials = await self.process_expired_trials(session)
        past_due = await self.process_past_due(session)
        timeouts = await self.process_pending_payment_timeout(session)
        result = {
            "expired_trials": len(expired_trials),
            "past_due_processed": len(past_due),
            "pending_payment_timeouts": len(timeouts),
        }
        if any(result.values()):
            logger.info("subscription_lifecycle_run", **result)
        return result
