from __future__ import annotations

from datetime import UTC, datetime

from sqlalchemy import delete, select, update
from sqlalchemy.ext.asyncio import AsyncSession

from backend.app.db.partner_profile import PartnerProfile
from backend.app.db.refresh_token_session import RefreshTokenSession
from backend.app.db.tenant import Tenant
from backend.app.db.tenant_membership import TenantMembership
from backend.app.db.user import User


class IdentityRepository:
    """Persistence helpers for the identity bounded context."""

    def __init__(self, session: AsyncSession) -> None:
        self.session = session

    async def get_user_by_email(self, email: str) -> User | None:
        return await self.session.scalar(select(User).where(User.email == email))

    async def get_user_by_id(self, user_id: str) -> User | None:
        return await self.session.scalar(select(User).where(User.id == user_id))

    async def get_user_by_telegram_id(self, telegram_id: int) -> User | None:
        return await self.session.scalar(
            select(User).where(User.telegram_id == str(telegram_id))
        )

    async def get_user_by_provider_id(self, provider_id: str, field: str) -> User | None:
        col = getattr(User, field, None)
        if col is None:
            return None
        return await self.session.scalar(select(User).where(col == provider_id))

    async def create_user(self, user: User) -> User:
        self.session.add(user)
        await self.session.flush()
        return user

    async def get_partner_profile_by_code(self, referral_code: str) -> PartnerProfile | None:
        return await self.session.scalar(
            select(PartnerProfile).where(PartnerProfile.referral_code == referral_code)
        )

    async def get_partner_profile_by_user(self, user_id: str) -> PartnerProfile | None:
        return await self.session.scalar(
            select(PartnerProfile).where(PartnerProfile.user_id == user_id)
        )

    async def create_partner_profile(self, profile: PartnerProfile) -> PartnerProfile:
        self.session.add(profile)
        await self.session.flush()
        return profile

    async def create_refresh_session(self, refresh_session: RefreshTokenSession) -> RefreshTokenSession:
        self.session.add(refresh_session)
        await self.session.flush()
        return refresh_session

    async def get_refresh_session(self, token_hash: str) -> RefreshTokenSession | None:
        return await self.session.scalar(
            select(RefreshTokenSession).where(RefreshTokenSession.token_id_hash == token_hash)
        )

    async def revoke_session_family(self, session_family_id: str, reason: str) -> None:
        await self.session.execute(
            update(RefreshTokenSession)
            .where(
                RefreshTokenSession.session_family_id == session_family_id,
                RefreshTokenSession.revoked_at.is_(None),
            )
            .values(revoked_at=datetime.now(UTC), revoked_reason=reason)
        )

    async def delete_expired_refresh_sessions(self, user_id: str) -> None:
        await self.session.execute(
            delete(RefreshTokenSession).where(
                RefreshTokenSession.user_id == user_id,
                RefreshTokenSession.revoked_at.is_not(None),
            )
        )

    async def list_memberships(self, user_id: str) -> list[tuple[TenantMembership, Tenant]]:
        rows = await self.session.execute(
            select(TenantMembership, Tenant)
            .join(Tenant, Tenant.id == TenantMembership.tenant_id)
            .where(TenantMembership.user_id == user_id)
            .order_by(TenantMembership.is_primary.desc(), Tenant.created_at.desc())
        )
        return list(rows.all())

    async def get_primary_membership(self, user_id: str) -> TenantMembership | None:
        return await self.session.scalar(
            select(TenantMembership)
            .where(TenantMembership.user_id == user_id)
            .order_by(TenantMembership.is_primary.desc(), TenantMembership.created_at.asc())
        )
