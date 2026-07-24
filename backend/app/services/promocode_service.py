from __future__ import annotations

from dataclasses import dataclass
from datetime import UTC, datetime

from fastapi import HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession

from backend.app.db.enums import PromoCodeKind
from backend.app.db.promo_code import PromoCode
from backend.app.db.promo_code_redemption import PromoCodeRedemption
from backend.app.db.subscription import Subscription
from backend.app.db.subscription_plan import SubscriptionPlan
from backend.app.db.user import User
from backend.app.repositories.promocode import PromoCodeRepository
from backend.app.schemas.promocode import (
    AppliedPromocodeResponse,
    ChangePromocode,
    CreatePromocode,
    PromocodePreviewResponse,
    PromocodeResponse,
)


@dataclass
class PromoQuote:
    promo_code: PromoCode
    original_price_amount: float
    discount_amount: float
    final_price_amount: float


class PromoCodeService:
    async def list_promocodes(self, session: AsyncSession) -> list[PromocodeResponse]:
        promo_codes = await PromoCodeRepository(session).list_all()
        return [self._to_response(item) for item in promo_codes]

    async def create_promocode(
        self,
        session: AsyncSession,
        current_user: User,
        payload: CreatePromocode,
    ) -> PromocodeResponse:
        repository = PromoCodeRepository(session)
        normalized_code = self._normalize_code(payload.code)
        if await repository.get_by_code(normalized_code):
            raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail="Promocode already exists")
        self._validate_dates(payload.start_time, payload.expire_time)
        self._validate_value(payload.type_promo, payload.value)

        promo_code = await repository.create(
            PromoCode(
                code=normalized_code,
                description=payload.description,
                kind=payload.type_promo,
                value=payload.value,
                max_uses=payload.max_uses,
                starts_at=payload.start_time,
                expires_at=payload.expire_time,
                is_active=payload.is_active,
                created_by_user_id=current_user.id,
            )
        )
        await session.commit()
        await session.refresh(promo_code)
        return self._to_response(promo_code)

    async def update_promocode(
        self,
        session: AsyncSession,
        code: str,
        payload: ChangePromocode,
    ) -> PromocodeResponse:
        promo_code = await self._get_promocode_or_404(session, code)
        fields_set = payload.model_fields_set

        if "description" in fields_set and payload.description is not None:
            promo_code.description = payload.description
        if "type_promo" in fields_set and payload.type_promo is not None:
            promo_code.kind = payload.type_promo
        if "value" in fields_set and payload.value is not None:
            promo_code.value = payload.value
        if "max_uses" in fields_set:
            promo_code.max_uses = payload.max_uses
        if "start_time" in fields_set:
            promo_code.starts_at = payload.start_time
        if "expire_time" in fields_set:
            promo_code.expires_at = payload.expire_time
        if "is_active" in fields_set and payload.is_active is not None:
            promo_code.is_active = payload.is_active

        self._validate_dates(promo_code.starts_at, promo_code.expires_at)
        self._validate_value(promo_code.kind, promo_code.value)

        await session.commit()
        await session.refresh(promo_code)
        return self._to_response(promo_code)

    async def delete_promocode(self, session: AsyncSession, code: str) -> None:
        promo_code = await self._get_promocode_or_404(session, code)
        await session.delete(promo_code)
        await session.commit()

    async def preview_promocode(
        self,
        session: AsyncSession,
        tenant_id: str,
        code: str,
        plan: SubscriptionPlan,
    ) -> PromocodePreviewResponse:
        quote = await self.quote_promocode(session, tenant_id, code, plan)
        return PromocodePreviewResponse(
            code=quote.promo_code.code,
            type_promo=quote.promo_code.kind,
            plan_code=plan.code,
            original_price_amount=quote.original_price_amount,
            discount_amount=quote.discount_amount,
            final_price_amount=quote.final_price_amount,
            remaining_uses=self._remaining_uses(quote.promo_code),
            is_valid=True,
        )

    async def quote_promocode(
        self,
        session: AsyncSession,
        tenant_id: str,
        code: str,
        plan: SubscriptionPlan,
    ) -> PromoQuote:
        promo_code = await self._get_promocode_or_404(session, code)
        self._assert_applicable(promo_code, tenant_id, await PromoCodeRepository(session).get_redemption(tenant_id, promo_code.id))
        original_price_amount = float(plan.price_amount)
        discount_amount = self._discount_amount(promo_code, original_price_amount)
        final_price_amount = max(0.0, round(original_price_amount - discount_amount, 2))
        return PromoQuote(
            promo_code=promo_code,
            original_price_amount=original_price_amount,
            discount_amount=discount_amount,
            final_price_amount=final_price_amount,
        )

    async def redeem_promocode(
        self,
        session: AsyncSession,
        current_user: User,
        tenant_id: str,
        subscription: Subscription,
        plan: SubscriptionPlan,
        code: str,
    ) -> PromoCodeRedemption:
        repository = PromoCodeRepository(session)
        quote = await self.quote_promocode(session, tenant_id, code, plan)
        quote.promo_code.uses_total += 1
        redemption = await repository.create_redemption(
            PromoCodeRedemption(
                tenant_id=tenant_id,
                promo_code_id=quote.promo_code.id,
                subscription_id=subscription.id,
                applied_by_user_id=current_user.id,
                plan_code=plan.code,
                original_price_amount=quote.original_price_amount,
                discount_amount=quote.discount_amount,
                final_price_amount=quote.final_price_amount,
            )
        )
        redemption.promo_code = quote.promo_code
        return redemption

    async def get_latest_redemption(
        self,
        session: AsyncSession,
        tenant_id: str,
    ) -> AppliedPromocodeResponse | None:
        redemption = await PromoCodeRepository(session).get_latest_redemption_for_tenant(tenant_id)
        return self.serialize_redemption(redemption)

    def serialize_redemption(
        self,
        redemption: PromoCodeRedemption | None,
    ) -> AppliedPromocodeResponse | None:
        if redemption is None or redemption.promo_code is None:
            return None
        return self._to_applied_response(redemption, redemption.promo_code)

    async def _get_promocode_or_404(self, session: AsyncSession, code: str) -> PromoCode:
        promo_code = await PromoCodeRepository(session).get_by_code(self._normalize_code(code))
        if promo_code is None:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Promocode not found")
        return promo_code

    def _assert_applicable(
        self,
        promo_code: PromoCode,
        tenant_id: str,
        redemption: PromoCodeRedemption | None,
    ) -> None:
        now = datetime.now(UTC)
        if not promo_code.is_active:
            raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail="Promocode is inactive")
        if promo_code.starts_at and self._to_utc(promo_code.starts_at) > now:
            raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail="Promocode is not active yet")
        if promo_code.expires_at and self._to_utc(promo_code.expires_at) <= now:
            raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail="Promocode has expired")
        if promo_code.max_uses is not None and promo_code.uses_total >= promo_code.max_uses:
            raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail="Promocode usage limit reached")
        if redemption is not None and redemption.tenant_id == tenant_id:
            raise HTTPException(
                status_code=status.HTTP_409_CONFLICT,
                detail="Promocode has already been redeemed for this tenant",
            )

    def _to_response(self, promo_code: PromoCode) -> PromocodeResponse:
        return PromocodeResponse(
            promo_code_id=promo_code.id,
            code=promo_code.code,
            description=promo_code.description,
            type_promo=promo_code.kind,
            value=promo_code.value,
            max_uses=promo_code.max_uses,
            uses_total=promo_code.uses_total,
            remaining_uses=self._remaining_uses(promo_code),
            start_time=promo_code.starts_at,
            expire_time=promo_code.expires_at,
            is_active=promo_code.is_active,
            created_by_user_id=promo_code.created_by_user_id,
            created_at=promo_code.created_at,
            updated_at=promo_code.updated_at,
        )

    def _to_applied_response(
        self,
        redemption: PromoCodeRedemption,
        promo_code: PromoCode,
    ) -> AppliedPromocodeResponse:
        return AppliedPromocodeResponse(
            code=promo_code.code,
            type_promo=promo_code.kind,
            original_price_amount=redemption.original_price_amount,
            discount_amount=redemption.discount_amount,
            final_price_amount=redemption.final_price_amount,
            redeemed_at=redemption.created_at,
        )

    def _discount_amount(self, promo_code: PromoCode, original_price_amount: float) -> float:
        if promo_code.kind == PromoCodeKind.PERCENT:
            return round(original_price_amount * (promo_code.value / 100), 2)
        if promo_code.kind == PromoCodeKind.GIFT_PLAN:
            return round(original_price_amount, 2)
        return round(min(float(promo_code.value), original_price_amount), 2)

    def _remaining_uses(self, promo_code: PromoCode) -> int | None:
        if promo_code.max_uses is None:
            return None
        return max(promo_code.max_uses - promo_code.uses_total, 0)

    def _normalize_code(self, code: str) -> str:
        return code.strip().upper()

    def _validate_dates(self, starts_at: datetime | None, expires_at: datetime | None) -> None:
        if starts_at and expires_at and expires_at <= starts_at:
            raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="expire_time must be later than start_time")

    def _validate_value(self, kind: PromoCodeKind, value: float) -> None:
        if kind == PromoCodeKind.PERCENT and not 0 < value <= 100:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="percent promo value must be between 0 and 100",
            )
        if kind != PromoCodeKind.GIFT_PLAN and value <= 0:
            raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="promo value must be greater than 0")

    def _to_utc(self, value: datetime) -> datetime:
        if value.tzinfo is None:
            return value.replace(tzinfo=UTC)
        return value.astimezone(UTC)
