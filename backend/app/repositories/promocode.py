from __future__ import annotations

from sqlalchemy import select
from sqlalchemy.orm import selectinload

from backend.app.db.promo_code import PromoCode
from backend.app.db.promo_code_redemption import PromoCodeRedemption
from backend.app.repositories.base import BaseRepository


class PromoCodeRepository(BaseRepository[PromoCode]):
    async def get_by_code(self, code: str) -> PromoCode | None:
        return await self.session.scalar(
            select(PromoCode)
            .options(selectinload(PromoCode.redemptions))
            .where(PromoCode.code == code)
        )

    async def list_all(self) -> list[PromoCode]:
        return list(
            (
                await self.session.scalars(
                    select(PromoCode)
                    .order_by(PromoCode.created_at.desc(), PromoCode.code.asc())
                )
            ).all()
        )

    async def create(self, promo_code: PromoCode) -> PromoCode:
        self.session.add(promo_code)
        await self.session.flush()
        return promo_code

    async def get_redemption(self, tenant_id: str, promo_code_id: str) -> PromoCodeRedemption | None:
        return await self.session.scalar(
            select(PromoCodeRedemption)
            .options(selectinload(PromoCodeRedemption.promo_code))
            .where(
                PromoCodeRedemption.tenant_id == tenant_id,
                PromoCodeRedemption.promo_code_id == promo_code_id,
            )
        )

    async def get_latest_redemption_for_tenant(self, tenant_id: str) -> PromoCodeRedemption | None:
        return await self.session.scalar(
            select(PromoCodeRedemption)
            .options(selectinload(PromoCodeRedemption.promo_code))
            .where(PromoCodeRedemption.tenant_id == tenant_id)
            .order_by(PromoCodeRedemption.created_at.desc())
        )

    async def create_redemption(self, redemption: PromoCodeRedemption) -> PromoCodeRedemption:
        self.session.add(redemption)
        await self.session.flush()
        return redemption
