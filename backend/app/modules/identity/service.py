from __future__ import annotations

import re
from datetime import UTC, datetime
from uuid import uuid4

from fastapi import HTTPException, status
from jose import JWTError
from redis.asyncio import Redis
from redis.exceptions import RedisError
from sqlalchemy.ext.asyncio import AsyncSession

from backend.app.core.configs import settings
from backend.app.core.crypto import encrypt_role_permissions
from backend.app.core.security import (
    create_access_token,
    create_refresh_token,
    decode_refresh_token,
    generate_numeric_otp,
    generate_referral_code,
    get_password_hash,
    hash_email_otp,
    hash_token_id,
    verify_password,
)
from backend.app.db.enums import AdminRole, ApprovalMode, MembershipRole, StrategyStatus, UserRole
from backend.app.modules.admin.rbac import ROLE_PERMISSIONS
from backend.app.db.approval_policy import ApprovalPolicy
from backend.app.db.partner_profile import PartnerProfile
from backend.app.db.project import Project
from backend.app.db.refresh_token_session import RefreshTokenSession
from backend.app.db.tenant import Tenant
from backend.app.db.tenant_membership import TenantMembership
from backend.app.db.user import User
from backend.app.modules.identity.repository import IdentityRepository
from backend.app.modules.identity.schemas import (
    ChangePasswordRequest,
    MembershipResponse,
    MessageResponse,
    PartnerReferralResponse,
    RegisterRequest,
    RegistrationAcceptedResponse,
    TokenResponse,
    UpdateMeRequest,
    UserResponse,
    VerifyEmailRequest,
)
from backend.app.modules.identity.verification_store import VerificationCodeStore
from backend.app.services.email_service import email_service

ADMIN_EMAIL = "admin@neuraai.io"


async def _exchange_oauth_code(
    token_url: str,
    code: str,
    client_id: str,
    client_secret: str,
    redirect_uri: str,
) -> dict:
    """Exchange an authorization code for OAuth tokens."""
    import httpx

    async with httpx.AsyncClient() as client:
        resp = await client.post(
            token_url,
            data={
                "code": code,
                "client_id": client_id,
                "client_secret": client_secret,
                "redirect_uri": redirect_uri,
                "grant_type": "authorization_code",
            },
            headers={"Accept": "application/json"},
        )
        if resp.status_code != 200:
            raise HTTPException(
                status_code=400,
                detail=f"Token exchange failed: {resp.text}",
            )
        return resp.json()


class IdentityService:
    """Application service for authentication, verification, and profile management."""

    async def register(
        self,
        session: AsyncSession,
        redis: Redis | None,
        payload: RegisterRequest,
    ) -> RegistrationAcceptedResponse:
        """Create or refresh a pending user registration and send an OTP code.

        Args:
            session: Active async SQLAlchemy session.
            redis: Redis client used for OTP storage.
            payload: User registration payload.

        Returns:
            RegistrationAcceptedResponse: Registration state for the client.
        """

        repository = IdentityRepository(session)
        user = await repository.get_user_by_email(str(payload.email))
        referred_by_user_id = await self._resolve_referral_owner(repository, payload.referral_code)

        if user and user.is_verified:
            raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail="Email already registered")

        if user is None:
            user = await repository.create_user(
                User(
                    email=str(payload.email),
                    password_hash=get_password_hash(payload.password),
                    full_name=payload.full_name,
                    phone=payload.phone,
                    role=UserRole.CLIENT,
                    is_active=True,
                    is_verified=False,
                    referred_by_user_id=referred_by_user_id,
                )
            )
        else:
            user.password_hash = get_password_hash(payload.password)
            user.full_name = payload.full_name
            user.phone = payload.phone
            user.referred_by_user_id = referred_by_user_id
            user.is_active = True
            user.is_verified = False

        partner_profile = await repository.get_partner_profile_by_user(user.id)
        if partner_profile is None:
            await repository.create_partner_profile(
                PartnerProfile(
                    user_id=user.id,
                    referral_code=generate_referral_code(user.full_name),
                    commission_rate=settings.billing.partner_commission_rate,
                )
            )

        await self._assign_admin_role_if_needed(user)
        await session.commit()
        return await self._issue_verification_code(redis, user)

    async def resend_verification(
        self,
        session: AsyncSession,
        redis: Redis | None,
        email: str,
    ) -> RegistrationAcceptedResponse:
        """Send a fresh OTP for a pending account."""

        repository = IdentityRepository(session)
        user = await repository.get_user_by_email(email)
        if user is None:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="User not found")
        if user.is_verified:
            raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail="Email is already verified")
        return await self._issue_verification_code(redis, user)

    async def verify_email(
        self,
        session: AsyncSession,
        redis: Redis | None,
        payload: VerifyEmailRequest,
        *,
        ip_address: str | None,
        user_agent: str | None,
    ) -> TokenResponse:
        """Confirm the OTP and issue the first access/refresh token pair."""

        repository = IdentityRepository(session)
        user = await repository.get_user_by_email(str(payload.email))
        if user is None:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="User not found")

        store = VerificationCodeStore(redis)
        record = await store.get(str(payload.email))
        if record is None or record.user_id != user.id:
            raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Verification code has expired")

        if record.attempts >= settings.security.email_verification_max_attempts:
            await store.delete(str(payload.email))
            raise HTTPException(
                status_code=status.HTTP_429_TOO_MANY_REQUESTS,
                detail="Too many verification attempts",
            )

        if record.code_hash != hash_email_otp(str(payload.email), payload.code):
            updated = await store.increment_attempts(str(payload.email))
            if updated and updated.attempts >= settings.security.email_verification_max_attempts:
                await store.delete(str(payload.email))
                raise HTTPException(
                    status_code=status.HTTP_429_TOO_MANY_REQUESTS,
                    detail="Too many verification attempts",
                )
            raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Invalid verification code")

        await store.delete(str(payload.email))
        user.is_verified = True
        user.last_login_at = datetime.now(UTC)
        await self._ensure_default_context(session, repository, user)
        await self._assign_admin_role_if_needed(user)
        await session.commit()
        return await self._issue_token_pair(
            session,
            user,
            ip_address=ip_address,
            user_agent=user_agent,
        )

    async def login(
        self,
        session: AsyncSession,
        redis: Redis | None,
        email: str,
        password: str,
        *,
        ip_address: str | None,
        user_agent: str | None,
        tenant_id: str | None = None,
    ) -> TokenResponse:
        """Authenticate a user with brute-force protection."""

        await self._enforce_login_rate_limit(redis, email, ip_address)
        repository = IdentityRepository(session)
        user = await repository.get_user_by_email(email)
        if not user or not verify_password(password, user.password_hash):
            raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Неверная почта или пароль")
        if not user.is_verified:
            raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Email is not verified")
        if not user.is_active:
            raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="User is disabled")

        user.last_login_at = datetime.now(UTC)

        if user.email in settings.admin.super_admin_emails:
            user.role = UserRole.ADMIN
            user.admin_role = AdminRole.SUPER_OWNER
            perms = list(ROLE_PERMISSIONS.get(AdminRole.SUPER_OWNER, set()))
            user.encrypted_permissions = encrypt_role_permissions(user.id, [p.value for p in perms])

        await session.commit()
        await self._clear_login_rate_limit(redis, email, ip_address)
        return await self._issue_token_pair(
            session,
            user,
            ip_address=ip_address,
            user_agent=user_agent,
            tenant_id=tenant_id,
        )

    async def admin_login(
        self,
        session: AsyncSession,
        login: str,
        password: str,
        *,
        ip_address: str | None,
        user_agent: str | None,
    ) -> TokenResponse:
        """Authenticate an admin by login/password (no registration)."""
        if not settings.web.admin_login or not settings.web.admin_password:
            raise HTTPException(status_code=501, detail="Admin login is not configured on this server")

        if login != settings.web.admin_login:
            raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid admin credentials")

        if password != settings.web.admin_password.get_secret_value():
            raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid admin credentials")

        repository = IdentityRepository(session)

        user = await repository.get_user_by_email(ADMIN_EMAIL)
        if not user:
            user = User(
                email=ADMIN_EMAIL,
                password_hash=get_password_hash(uuid4().hex),
                full_name="Administrator",
                role=UserRole.ADMIN,
                admin_role=AdminRole.SUPER_OWNER,
                is_active=True,
                is_verified=True,
            )
            session.add(user)
            await session.flush()

        user.role = UserRole.ADMIN
        user.admin_role = AdminRole.SUPER_OWNER
        user.is_active = True
        user.is_verified = True
        user.last_login_at = datetime.now(UTC)

        perms = list(ROLE_PERMISSIONS.get(AdminRole.SUPER_OWNER, set()))
        user.encrypted_permissions = encrypt_role_permissions(user.id, [p.value for p in perms])

        await session.commit()
        return await self._issue_token_pair(
            session,
            user,
            ip_address=ip_address,
            user_agent=user_agent,
        )

    async def _oauth_login(
        self,
        session: AsyncSession,
        provider: str,
        provider_id: str,
        email: str | None,
        name: str | None,
        avatar: str | None,
        ip_address: str | None,
        user_agent: str | None,
    ) -> TokenResponse:
        """Generic OAuth login — create or update user by provider ID."""
        id_field_map = {"vk": "vk_id", "yandex": "yandex_id", "mailru": "mailru_id"}
        id_field = id_field_map.get(provider)
        if not id_field:
            raise HTTPException(status_code=400, detail=f"Unknown provider: {provider}")

        repository = IdentityRepository(session)

        user = await repository.get_user_by_provider_id(provider_id, id_field)

        if not user and email:
            user = await repository.get_user_by_email(email)
            if user:
                setattr(user, id_field, provider_id)

        if not user:
            user_email = email or f"{provider}_{provider_id}@{provider}.neura"
            user = await repository.create_user(
                User(
                    email=user_email,
                    password_hash="",
                    full_name=name or user_email.split("@")[0],
                    **{id_field: provider_id},
                    avatar_url=avatar or None,
                    role=UserRole.CLIENT,
                    is_active=True,
                    is_verified=True,
                )
            )
            await session.flush()
            await self._ensure_default_context(session, repository, user)

        if avatar and not user.avatar_url:
            user.avatar_url = avatar
        user.last_login_at = datetime.now(UTC)
        await self._assign_admin_role_if_needed(user)
        await session.commit()
        return await self._issue_token_pair(
            session, user, ip_address=ip_address, user_agent=user_agent,
        )

    async def vk_login(
        self,
        session: AsyncSession,
        code: str,
        redirect_uri: str,
        *,
        ip_address: str | None,
        user_agent: str | None,
    ) -> TokenResponse:
        if not settings.oauth.vk.configured:
            raise HTTPException(status_code=400, detail="VK OAuth is not configured")
        import httpx

        token_resp = await _exchange_oauth_code(
            token_url="https://oauth.vk.com/access_token",
            code=code,
            client_id=settings.oauth.vk.client_id,
            client_secret=settings.oauth.vk.client_secret.get_secret_value(),
            redirect_uri=redirect_uri,
        )
        access_token = token_resp.get("access_token")
        vk_user_id = str(token_resp.get("user_id", ""))
        email = token_resp.get("email")
        if not access_token or not vk_user_id:
            raise HTTPException(status_code=400, detail="VK returned no user_id")

        async with httpx.AsyncClient() as client:
            user_resp = await client.get(
                "https://api.vk.com/method/users.get",
                params={
                    "user_ids": vk_user_id,
                    "fields": "photo_200,first_name,last_name",
                    "access_token": access_token,
                    "v": "5.199",
                },
            )
            user_data = user_resp.json()
        first_name = ""
        last_name = ""
        avatar = None
        if user_data.get("response"):
            u = user_data["response"][0]
            first_name = u.get("first_name", "")
            last_name = u.get("last_name", "")
            avatar = u.get("photo_200")

        return await self._oauth_login(
            session, "vk", vk_user_id, email,
            name=f"{first_name} {last_name}".strip() or None,
            avatar=avatar,
            ip_address=ip_address, user_agent=user_agent,
        )

    async def yandex_login(
        self,
        session: AsyncSession,
        code: str,
        redirect_uri: str,
        *,
        ip_address: str | None,
        user_agent: str | None,
    ) -> TokenResponse:
        if not settings.oauth.yandex.configured:
            raise HTTPException(status_code=400, detail="Yandex OAuth is not configured")
        import httpx

        token_resp = await _exchange_oauth_code(
            token_url="https://oauth.yandex.ru/token",
            code=code,
            client_id=settings.oauth.yandex.client_id,
            client_secret=settings.oauth.yandex.client_secret.get_secret_value(),
            redirect_uri=redirect_uri,
        )
        access_token = token_resp.get("access_token")
        if not access_token:
            raise HTTPException(status_code=400, detail="Yandex returned no access_token")

        async with httpx.AsyncClient() as client:
            user_resp = await client.get(
                "https://login.yandex.ru/info?format=json",
                headers={"Authorization": f"OAuth {access_token}"},
            )
            info = user_resp.json()
        yandex_id = str(info.get("id", ""))
        email = info.get("default_email")
        name = info.get("real_name") or info.get("display_name")
        avatar_url = None
        if info.get("default_avatar_id"):
            avatar_url = f"https://avatars.yandex.net/get-yapic/{info['default_avatar_id']}/islands-200"

        return await self._oauth_login(
            session, "yandex", yandex_id, email,
            name=name, avatar=avatar_url,
            ip_address=ip_address, user_agent=user_agent,
        )

    async def mailru_login(
        self,
        session: AsyncSession,
        code: str,
        redirect_uri: str,
        *,
        ip_address: str | None,
        user_agent: str | None,
    ) -> TokenResponse:
        if not settings.oauth.mailru.configured:
            raise HTTPException(status_code=400, detail="Mail.ru OAuth is not configured")
        import httpx

        token_resp = await _exchange_oauth_code(
            token_url="https://oauth.mail.ru/token",
            code=code,
            client_id=settings.oauth.mailru.client_id,
            client_secret=settings.oauth.mailru.client_secret.get_secret_value(),
            redirect_uri=redirect_uri,
        )
        access_token = token_resp.get("access_token")
        if not access_token:
            raise HTTPException(status_code=400, detail="Mail.ru returned no access_token")

        async with httpx.AsyncClient() as client:
            user_resp = await client.get(
                "https://oauth.mail.ru/userinfo",
                headers={"Authorization": f"Bearer {access_token}"},
            )
            info = user_resp.json()
        mailru_id = str(info.get("id", "") or info.get("email", ""))
        email = info.get("email")
        name = info.get("name") or f"{info.get('first_name', '')} {info.get('last_name', '')}".strip() or None
        avatar = info.get("image") or info.get("picture")

        return await self._oauth_login(
            session, "mailru", mailru_id, email,
            name=name, avatar=avatar,
            ip_address=ip_address, user_agent=user_agent,
        )

    async def telegram_login(
        self,
        session: AsyncSession,
        telegram_id: int,
        first_name: str,
        last_name: str | None,
        username: str | None,
        photo_url: str | None,
        *,
        ip_address: str | None,
        user_agent: str | None,
    ) -> TokenResponse:
        """Authenticate via Telegram Login Widget data."""
        repository = IdentityRepository(session)
        user = await repository.get_user_by_telegram_id(telegram_id)

        if user:
            if username:
                user.full_name = username
        else:
            email = f"tg_{telegram_id}@telegram.neura"
            name = f"{first_name} {last_name or ''}".strip() or username or f"tg_{telegram_id}"
            user = await repository.create_user(
                User(
                    email=email,
                    password_hash="",
                    full_name=name,
                    telegram_id=str(telegram_id),
                    avatar_url=photo_url or None,
                    role=UserRole.CLIENT,
                    is_active=True,
                    is_verified=True,
                )
            )
            await session.flush()
            await self._ensure_default_context(session, repository, user)

        user.last_login_at = datetime.now(UTC)
        await self._assign_admin_role_if_needed(user)
        await session.commit()
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
        ip_address: str | None,
        user_agent: str | None,
    ) -> TokenResponse:
        """Rotate a refresh token and issue a new access token pair."""

        repository = IdentityRepository(session)
        try:
            payload = decode_refresh_token(refresh_token)
        except JWTError as exc:
            raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid refresh token") from exc

        if not payload.token_id:
            raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid refresh token")

        refresh_session = await repository.get_refresh_session(hash_token_id(payload.token_id))
        now = datetime.now(UTC)
        if refresh_session is None or refresh_session.user_id != payload.subject:
            raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Refresh token is unavailable")

        if refresh_session.revoked_at is not None:
            if refresh_session.session_family_id:
                await repository.revoke_session_family(refresh_session.session_family_id, "token_reuse_detected")
                await session.commit()
            raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Refresh token has been revoked")

        if self._to_utc(refresh_session.expires_at) <= now:
            refresh_session.revoked_at = now
            refresh_session.revoked_reason = "expired"
            await session.commit()
            raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Refresh token expired")

        if not self._is_matching_fingerprint(refresh_session.user_agent, user_agent, refresh_session.ip_address, ip_address):
            await repository.revoke_session_family(refresh_session.session_family_id, "fingerprint_mismatch")
            await session.commit()
            raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Session fingerprint mismatch")

        user = await repository.get_user_by_id(payload.subject)
        if not user or not user.is_active or not user.is_verified:
            raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="User unavailable")

        refresh_session.revoked_at = now
        refresh_session.revoked_reason = "rotated"
        refresh_session.last_used_at = now
        return await self._issue_token_pair(
            session,
            user,
            ip_address=ip_address,
            user_agent=user_agent,
            tenant_id=refresh_session.tenant_id,
            session_family_id=refresh_session.session_family_id,
        )

    async def logout(self, session: AsyncSession, refresh_token: str) -> MessageResponse:
        """Revoke the refresh token session."""

        repository = IdentityRepository(session)
        try:
            payload = decode_refresh_token(refresh_token)
        except JWTError as exc:
            raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid refresh token") from exc

        if payload.token_id:
            refresh_session = await repository.get_refresh_session(hash_token_id(payload.token_id))
            if refresh_session and refresh_session.revoked_at is None:
                refresh_session.revoked_at = datetime.now(UTC)
                refresh_session.revoked_reason = "logout"
                await session.commit()

        return MessageResponse(message="Logged out successfully", timestamp=datetime.now(UTC))

    async def get_profile(self, session: AsyncSession, current_user: User) -> UserResponse:
        """Return the authenticated user profile with memberships."""

        repository = IdentityRepository(session)
        role_assigned = await self._assign_admin_role_if_needed(current_user)
        if role_assigned:
            await session.commit()
        memberships = await repository.list_memberships(current_user.id)
        return UserResponse(
            user_id=current_user.id,
            email=current_user.email,
            full_name=current_user.full_name,
            phone=current_user.phone,
            role=current_user.role.value,
            admin_role=current_user.admin_role.value if current_user.admin_role else None,
            is_active=current_user.is_active,
            is_verified=current_user.is_verified,
            memberships=[
                MembershipResponse(
                    tenant_id=tenant.id,
                    tenant_name=tenant.name,
                    tenant_slug=tenant.slug,
                    role=membership.role.value,
                    is_primary=membership.is_primary,
                )
                for membership, tenant in memberships
            ],
        )

    async def update_profile(
        self,
        session: AsyncSession,
        current_user: User,
        payload: UpdateMeRequest,
    ) -> UserResponse:
        """Update mutable user profile fields."""

        if payload.full_name is not None:
            current_user.full_name = payload.full_name
        if payload.phone is not None:
            current_user.phone = payload.phone
        await session.commit()
        return await self.get_profile(session, current_user)

    async def change_password(
        self,
        session: AsyncSession,
        current_user: User,
        payload: ChangePasswordRequest,
    ) -> MessageResponse:
        """Rotate the current user password."""

        if not verify_password(payload.current_password, current_user.password_hash):
            raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid current password")
        current_user.password_hash = get_password_hash(payload.new_password)
        
        # Revoke all other refresh token sessions for security
        repository = IdentityRepository(session)
        await repository.revoke_all_sessions_for_user(
            current_user.id,
            reason="password_changed",
        )

        await session.commit()
        await email_service.send_password_changed_notification(
            to=current_user.email,
            full_name=current_user.full_name,
        )
        return MessageResponse(message="Password changed successfully", timestamp=datetime.now(UTC))

    async def get_partner_referral(
        self,
        session: AsyncSession,
        current_user: User,
    ) -> PartnerReferralResponse:
        """Return the referral details for the authenticated user."""

        repository = IdentityRepository(session)
        profile = await repository.get_partner_profile_by_user(current_user.id)
        if not profile:
            profile = await repository.create_partner_profile(
                PartnerProfile(
                    user_id=current_user.id,
                    referral_code=generate_referral_code(current_user.full_name),
                    commission_rate=settings.billing.partner_commission_rate,
                )
            )
            await session.commit()

        return PartnerReferralResponse(
            referral_code=profile.referral_code,
            referral_link=f"{settings.web.public_base_url.rstrip('/')}/ref/{profile.referral_code}",
            commission_rate=profile.commission_rate,
            total_income=profile.total_income,
            pending_payout=profile.pending_payout,
        )

    async def _issue_verification_code(
        self,
        redis: Redis | None,
        user: User,
    ) -> RegistrationAcceptedResponse:
        code = generate_numeric_otp()
        store = VerificationCodeStore(redis)
        ttl_seconds = settings.security.email_verification_ttl_seconds
        await store.save(
            user.email,
            store.build_record(user.id, hash_email_otp(user.email, code), ttl_seconds),
            ttl_seconds,
        )
        await email_service.send_verification_code(
            to=user.email,
            code=code,
            full_name=user.full_name,
        )
        return RegistrationAcceptedResponse(
            message="Verification code sent",
            email=user.email,
            verification_ttl_seconds=ttl_seconds,
            debug_code=code if settings.app.env == "local" else None,
        )

    async def _issue_token_pair(
        self,
        session: AsyncSession,
        user: User,
        *,
        ip_address: str | None,
        user_agent: str | None,
        tenant_id: str | None = None,
        session_family_id: str | None = None,
    ) -> TokenResponse:
        """Create and persist a new refresh session with rotation metadata."""

        repository = IdentityRepository(session)
        active_tenant_id = tenant_id or await self._resolve_active_tenant_id(repository, user.id)
        access_token, expires_in = create_access_token(user.id, user.role.value, tenant_id=active_tenant_id)
        refresh_token, refresh_token_id, refresh_expires_in, refresh_expires_at = create_refresh_token(user.id)
        await repository.create_refresh_session(
            RefreshTokenSession(
                user_id=user.id,
                token_id_hash=hash_token_id(refresh_token_id),
                tenant_id=active_tenant_id,
                ip_address=ip_address,
                user_agent=user_agent,
                session_family_id=session_family_id or str(uuid4()),
                expires_at=refresh_expires_at,
                last_used_at=datetime.now(UTC),
            )
        )
        await session.commit()
        return TokenResponse(
            access_token=access_token,
            refresh_token=refresh_token,
            expires_in=expires_in,
            refresh_expires_in=refresh_expires_in,
            user=await self.get_profile(session, user),
        )

    async def _resolve_referral_owner(
        self,
        repository: IdentityRepository,
        referral_code: str | None,
    ) -> str | None:
        if not referral_code:
            return None
        referrer = await repository.get_partner_profile_by_code(referral_code)
        return referrer.user_id if referrer else None

    async def _resolve_active_tenant_id(self, repository: IdentityRepository, user_id: str) -> str | None:
        membership = await repository.get_primary_membership(user_id)
        return membership.tenant_id if membership else None

    async def _enforce_login_rate_limit(
        self,
        redis: Redis | None,
        email: str,
        ip_address: str | None,
    ) -> None:
        if redis is None:
            return
        key = self._login_limit_key(email, ip_address)
        try:
            current = await redis.incr(key)
            if current == 1:
                await redis.expire(key, 60)
            if current > settings.rate_limit.login_attempts_per_minute:
                raise HTTPException(
                    status_code=status.HTTP_429_TOO_MANY_REQUESTS,
                    detail="Too many login attempts",
                )
        except RedisError:
            return

    async def _clear_login_rate_limit(
        self,
        redis: Redis | None,
        email: str,
        ip_address: str | None,
    ) -> None:
        if redis is None:
            return
        try:
            await redis.delete(self._login_limit_key(email, ip_address))
        except RedisError:
            return

    def _login_limit_key(self, email: str, ip_address: str | None) -> str:
        normalized_email = email.strip().lower()
        client_ip = ip_address or "unknown"
        return f"auth:login-attempts:{normalized_email}:{client_ip}"

    def _is_matching_fingerprint(
        self,
        stored_user_agent: str | None,
        current_user_agent: str | None,
        stored_ip_address: str | None,
        current_ip_address: str | None,
    ) -> bool:
        if stored_user_agent and current_user_agent and stored_user_agent != current_user_agent:
            return False
        if stored_ip_address and current_ip_address and stored_ip_address != current_ip_address:
            return False
        return True

    async def _assign_admin_role_if_needed(self, user: User) -> bool:
        """Проверяет, является ли email супер-админом, и назначает роль."""
        if user.email in settings.admin.super_admin_emails and user.admin_role is None:
            user.role = UserRole.ADMIN
            user.admin_role = AdminRole.SUPER_OWNER
            perms = list(ROLE_PERMISSIONS.get(AdminRole.SUPER_OWNER, set()))
            user.encrypted_permissions = encrypt_role_permissions(user.id, [p.value for p in perms])
            return True
        return False

    async def _ensure_default_context(
        self,
        session: AsyncSession,
        repository: IdentityRepository,
        user: User,
    ) -> None:
        membership = await repository.get_primary_membership(user.id)
        if membership is not None:
            return
        slug_base = (
            re.sub(r"[^a-z0-9]+", "-", (user.full_name or user.email.split("@")[0]).strip().lower()).strip("-")
            or "user"
        )
        tenant = Tenant(
            slug=f"{slug_base}-{uuid4().hex[:8]}",
            name=user.full_name or f"Business of {user.email}",
            owner_user_id=user.id,
            default_timezone="UTC",
            industry="other",
            search_document=user.email,
        )
        session.add(tenant)
        await session.flush()
        session.add(
            TenantMembership(
                tenant_id=tenant.id,
                user_id=user.id,
                role=MembershipRole.OWNER,
                is_primary=True,
            )
        )
        project = Project(
            tenant_id=tenant.id,
            owner_user_id=user.id,
            company_name=user.full_name or "My Business",
            business_description="Business profile not yet completed",
            city="Not set",
            industry="other",
            target_audience="Not yet defined",
            strategy_status=StrategyStatus.DRAFT,
        )
        session.add(project)
        await session.flush()
        session.add(
            ApprovalPolicy(
                tenant_id=tenant.id,
                project_id=project.id,
                mode=ApprovalMode.MANUAL,
            )
        )

    def _to_utc(self, value: datetime) -> datetime:
        if value.tzinfo is None:
            return value.replace(tzinfo=UTC)
        return value.astimezone(UTC)
