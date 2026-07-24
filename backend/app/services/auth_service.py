from __future__ import annotations

from datetime import UTC, datetime

from fastapi import HTTPException, status
from jose import JWTError
from sqlalchemy.ext.asyncio import AsyncSession

from backend.app.core.security import (
    create_access_token,
    create_refresh_token,
    decode_refresh_token,
    generate_referral_code,
    get_password_hash,
    hash_token_id,
    verify_password,
)
from backend.app.db.enums import UserRole
from backend.app.db.partner_profile import PartnerProfile
from backend.app.db.refresh_token_session import RefreshTokenSession
from backend.app.db.user import User
from backend.app.repositories.auth import RefreshSessionRepository
from backend.app.repositories.user import PartnerProfileRepository, UserRepository
from backend.app.schemas.auth import (
    LoginRequest,
    LogoutRequest,
    MessageResponse,
    RegisterRequest,
    TokenResponse,
    UserPublic,
)


class AuthService:
    async def register(
        self,
        session: AsyncSession,
        payload: RegisterRequest,
        *,
        ip_address: str | None = None,
        user_agent: str | None = None,
    ) -> TokenResponse:
        user_repository = UserRepository(session)
        partner_repository = PartnerProfileRepository(session)

        existing_user = await user_repository.get_by_email(str(payload.email))
        if existing_user:
            raise HTTPException(
                status_code=status.HTTP_409_CONFLICT,
                detail="User with this email already exists",
            )

        referred_by_user_id = await self._resolve_referral_owner(
            partner_repository,
            payload.referral_code,
        )

        user = User(
            email=str(payload.email),
            password_hash=get_password_hash(payload.password),
            full_name=payload.full_name,
            phone=payload.phone,
            company_name=payload.company_name,
            role=UserRole.CLIENT,
            referred_by_user_id=referred_by_user_id,
        )
        await user_repository.create(user)

        await partner_repository.create(
            PartnerProfile(
                user_id=user.id,
                referral_code=generate_referral_code(payload.full_name),
            ),
        )
        return await self._issue_token_pair(
            session,
            user,
            ip_address=ip_address,
            user_agent=user_agent,
        )

    async def login(
        self,
        session: AsyncSession,
        payload: LoginRequest,
        *,
        ip_address: str | None = None,
        user_agent: str | None = None,
    ) -> TokenResponse:
        user = await UserRepository(session).get_by_email(str(payload.email))
        if not user or not verify_password(payload.password, user.password_hash):
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Invalid email or password",
            )
        if not user.is_active:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="User account is disabled",
            )

        return await self._issue_token_pair(
            session,
            user,
            ip_address=ip_address,
            user_agent=user_agent,
        )

    async def refresh(
        self,
        session: AsyncSession,
        refresh_token: str,
        *,
        ip_address: str | None = None,
        user_agent: str | None = None,
    ) -> TokenResponse:
        try:
            payload = decode_refresh_token(refresh_token)
        except JWTError as exc:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Invalid refresh token",
            ) from exc
        if not payload.token_id:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Invalid refresh token",
            )

        refresh_repository = RefreshSessionRepository(session)
        user_repository = UserRepository(session)
        token_session = await refresh_repository.get_by_token_hash(
            hash_token_id(payload.token_id)
        )
        if (
            not token_session
            or token_session.user_id != payload.subject
            or token_session.revoked_at is not None
            or self._to_utc(token_session.expires_at) <= datetime.now(UTC)
        ):
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Refresh token is expired or revoked",
            )

        user = await user_repository.get_by_id(payload.subject)
        if not user or not user.is_active:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="User is not available",
            )

        replacement_token, replacement_token_id, refresh_expires_in, refresh_expires_at = (
            create_refresh_token(user.id)
        )
        access_token, expires_in = create_access_token(user.id, user.role.value)

        token_session.revoked_at = datetime.now(UTC)
        token_session.replaced_by_token_id_hash = hash_token_id(replacement_token_id)

        await refresh_repository.create(
            RefreshTokenSession(
                user_id=user.id,
                token_id_hash=hash_token_id(replacement_token_id),
                user_agent=user_agent,
                ip_address=ip_address,
                expires_at=refresh_expires_at,
            ),
        )
        await session.commit()

        return TokenResponse(
            access_token=access_token,
            refresh_token=replacement_token,
            expires_in=expires_in,
            refresh_expires_in=refresh_expires_in,
            user=self._to_user_public(user),
        )

    async def logout(
        self,
        session: AsyncSession,
        payload: LogoutRequest,
    ) -> MessageResponse:
        try:
            token_payload = decode_refresh_token(payload.refresh_token)
        except JWTError as exc:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Invalid refresh token",
            ) from exc
        if token_payload.token_id:
            token_session = await RefreshSessionRepository(session).get_by_token_hash(
                hash_token_id(token_payload.token_id)
            )
            if token_session and token_session.revoked_at is None:
                token_session.revoked_at = datetime.now(UTC)
                await session.commit()

        return MessageResponse(message="Logged out successfully")

    async def _issue_token_pair(
        self,
        session: AsyncSession,
        user: User,
        *,
        ip_address: str | None,
        user_agent: str | None,
    ) -> TokenResponse:
        refresh_repository = RefreshSessionRepository(session)
        access_token, expires_in = create_access_token(user.id, user.role.value)
        refresh_token, refresh_token_id, refresh_expires_in, refresh_expires_at = (
            create_refresh_token(user.id)
        )

        await refresh_repository.create(
            RefreshTokenSession(
                user_id=user.id,
                token_id_hash=hash_token_id(refresh_token_id),
                user_agent=user_agent,
                ip_address=ip_address,
                expires_at=refresh_expires_at,
            ),
        )
        await session.commit()

        return TokenResponse(
            access_token=access_token,
            refresh_token=refresh_token,
            expires_in=expires_in,
            refresh_expires_in=refresh_expires_in,
            user=self._to_user_public(user),
        )

    async def _resolve_referral_owner(
        self,
        partner_repository: PartnerProfileRepository,
        referral_code: str | None,
    ) -> str | None:
        if not referral_code:
            return None

        partner_profile = await partner_repository.get_by_referral_code(referral_code)
        return partner_profile.user_id if partner_profile else None

    def _to_user_public(self, user: User) -> UserPublic:
        return UserPublic(
            user_id=user.id,
            email=user.email,
            full_name=user.full_name,
            phone=user.phone,
            company_name=user.company_name,
            role=user.role.value,
            is_active=user.is_active,
        )

    def _to_utc(self, value: datetime) -> datetime:
        if value.tzinfo is None:
            return value.replace(tzinfo=UTC)
        return value.astimezone(UTC)
