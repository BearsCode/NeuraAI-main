from __future__ import annotations

from sqlalchemy import select

from backend.app.db.partner_profile import PartnerProfile
from backend.app.db.user import User
from backend.app.repositories.base import BaseRepository


class UserRepository(BaseRepository[User]):
    async def get_by_id(self, user_id: str) -> User | None:
        return await self.session.scalar(select(User).where(User.id == user_id))

    async def get_by_email(self, email: str) -> User | None:
        return await self.session.scalar(select(User).where(User.email == email))

    async def create(self, user: User) -> User:
        self.session.add(user)
        await self.session.flush()
        return user


class PartnerProfileRepository(BaseRepository[PartnerProfile]):
    async def get_by_user_id(self, user_id: str) -> PartnerProfile | None:
        return await self.session.scalar(
            select(PartnerProfile).where(PartnerProfile.user_id == user_id)
        )

    async def get_by_referral_code(self, referral_code: str) -> PartnerProfile | None:
        return await self.session.scalar(
            select(PartnerProfile).where(PartnerProfile.referral_code == referral_code)
        )

    async def create(self, profile: PartnerProfile) -> PartnerProfile:
        self.session.add(profile)
        await self.session.flush()
        return profile
