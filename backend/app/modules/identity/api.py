from __future__ import annotations

from datetime import UTC, datetime

from fastapi import APIRouter, Body, Depends, HTTPException, Request, Response, status
from fastapi.security import OAuth2PasswordRequestForm
from sqlalchemy.ext.asyncio import AsyncSession

from backend.app.api.deps import get_current_user
from backend.app.core.database import get_db_session
from backend.app.core.configs import settings
from backend.app.db.user import User
from backend.app.modules.identity.schemas import (
    AdminLoginRequest,
    ChangePasswordRequest,
    MailruCallbackRequest,
    VKCallbackRequest,
    YandexCallbackRequest,
    LoginRequest,
    LogoutRequest,
    MessageResponse,
    PartnerReferralResponse,
    RefreshRequest,
    RegisterRequest,
    RegistrationAcceptedResponse,
    ResendVerificationRequest,
    TelegramLoginRequest,
    TokenResponse,
    UpdateMeRequest,
    UserResponse,
    VerifyEmailRequest,
)
from backend.app.modules.identity.service import IdentityService

router = APIRouter(prefix="/identity", tags=["identity"])
legacy_router = APIRouter(prefix="/auth", tags=["auth"])
service = IdentityService()


@router.post("/register", response_model=RegistrationAcceptedResponse, status_code=status.HTTP_201_CREATED)
@legacy_router.post("/register", response_model=RegistrationAcceptedResponse, status_code=status.HTTP_201_CREATED)
async def register(
    payload: RegisterRequest,
    request: Request,
    session: AsyncSession = Depends(get_db_session),
) -> RegistrationAcceptedResponse:
    return await service.register(session, request.app.state.redis, payload)


@router.post("/verify-email", response_model=TokenResponse)
@legacy_router.post("/verify-email", response_model=TokenResponse)
async def verify_email(
    payload: VerifyEmailRequest,
    request: Request,
    response: Response,
    session: AsyncSession = Depends(get_db_session),
) -> TokenResponse:
    result = await service.verify_email(
        session,
        request.app.state.redis,
        payload,
        ip_address=request.client.host if request.client else None,
        user_agent=request.headers.get("user-agent"),
    )
    _attach_docs_auth_cookies(request, response, result)
    return result


@router.post("/resend-verification", response_model=RegistrationAcceptedResponse)
@legacy_router.post("/resend-verification", response_model=RegistrationAcceptedResponse)
async def resend_verification(
    payload: ResendVerificationRequest,
    request: Request,
    session: AsyncSession = Depends(get_db_session),
) -> RegistrationAcceptedResponse:
    return await service.resend_verification(session, request.app.state.redis, str(payload.email))


@router.post("/test-verify", response_model=MessageResponse)
@legacy_router.post("/test-verify", response_model=MessageResponse)
async def test_verify_user(
    email: str = Body(..., embed=True),
    session: AsyncSession = Depends(get_db_session),
) -> MessageResponse:
    """DEV ONLY: verify a user by email without OTP. Enabled only in local/dev env."""
    from sqlalchemy import select
    from backend.app.db.user import User

    if settings.app.env not in ("local", "dev"):
        raise HTTPException(status_code=403, detail="Only available in local/dev environment")

    result = await session.execute(select(User).where(User.email == email))
    user = result.scalar_one_or_none()
    if not user:
        raise HTTPException(status_code=404, detail="User not found")

    user.is_verified = True
    await session.commit()
    return MessageResponse(
        message=f"User {email} verified successfully",
        timestamp=datetime.now(UTC),
    )


@router.post("/oauth/vk/callback", response_model=TokenResponse)
@legacy_router.post("/oauth/vk/callback", response_model=TokenResponse)
async def vk_callback(
    payload: VKCallbackRequest,
    request: Request,
    response: Response,
    session: AsyncSession = Depends(get_db_session),
) -> TokenResponse:
    result = await service.vk_login(
        session,
        code=payload.code,
        redirect_uri=payload.redirect_uri,
        ip_address=request.client.host if request.client else None,
        user_agent=request.headers.get("user-agent"),
    )
    _attach_docs_auth_cookies(request, response, result)
    return result


@router.post("/oauth/yandex/callback", response_model=TokenResponse)
@legacy_router.post("/oauth/yandex/callback", response_model=TokenResponse)
async def yandex_callback(
    payload: YandexCallbackRequest,
    request: Request,
    response: Response,
    session: AsyncSession = Depends(get_db_session),
) -> TokenResponse:
    result = await service.yandex_login(
        session,
        code=payload.code,
        redirect_uri=payload.redirect_uri,
        ip_address=request.client.host if request.client else None,
        user_agent=request.headers.get("user-agent"),
    )
    _attach_docs_auth_cookies(request, response, result)
    return result


@router.post("/oauth/mailru/callback", response_model=TokenResponse)
@legacy_router.post("/oauth/mailru/callback", response_model=TokenResponse)
async def mailru_callback(
    payload: MailruCallbackRequest,
    request: Request,
    response: Response,
    session: AsyncSession = Depends(get_db_session),
) -> TokenResponse:
    result = await service.mailru_login(
        session,
        code=payload.code,
        redirect_uri=payload.redirect_uri,
        ip_address=request.client.host if request.client else None,
        user_agent=request.headers.get("user-agent"),
    )
    _attach_docs_auth_cookies(request, response, result)
    return result


@router.post("/oauth/telegram", response_model=TokenResponse)
@legacy_router.post("/oauth/telegram", response_model=TokenResponse)
async def telegram_login(
    payload: TelegramLoginRequest,
    request: Request,
    response: Response,
    session: AsyncSession = Depends(get_db_session),
) -> TokenResponse:
    if not settings.oauth.telegram_login.configured:
        raise HTTPException(status_code=400, detail="Telegram Login is not configured")

    from hashlib import sha256
    import hmac

    bot_token = settings.oauth.telegram_login.bot_token.get_secret_value()
    secret_key = sha256(bot_token.encode()).digest()
    check_list = [
        f"auth_date={payload.auth_date}",
        f"first_name={payload.first_name}",
        f"id={payload.id}",
        f"last_name={payload.last_name}" if payload.last_name else "",
        f"photo_url={payload.photo_url}" if payload.photo_url else "",
        f"username={payload.username}" if payload.username else "",
    ]
    check_string = "\n".join(sorted([s for s in check_list if s]))
    computed_hash = hmac.new(secret_key, check_string.encode(), sha256).hexdigest()

    if computed_hash != payload.hash:
        raise HTTPException(status_code=400, detail="Invalid Telegram login data")

    result = await service.telegram_login(
        session,
        telegram_id=payload.id,
        first_name=payload.first_name,
        last_name=payload.last_name,
        username=payload.username,
        photo_url=payload.photo_url,
        ip_address=request.client.host if request.client else None,
        user_agent=request.headers.get("user-agent"),
    )
    _attach_docs_auth_cookies(request, response, result)
    return result


@router.post("/login", response_model=TokenResponse)
@legacy_router.post("/login", response_model=TokenResponse)
async def login(
    payload: LoginRequest,
    request: Request,
    response: Response,
    session: AsyncSession = Depends(get_db_session),
) -> TokenResponse:
    result = await service.login(
        session,
        request.app.state.redis,
        email=str(payload.email),
        password=payload.password,
        tenant_id=payload.tenant_id or request.headers.get("X-Tenant-ID"),
        ip_address=request.client.host if request.client else None,
        user_agent=request.headers.get("user-agent"),
    )
    _attach_docs_auth_cookies(request, response, result)
    return result


@router.post("/admin-login", response_model=TokenResponse)
@legacy_router.post("/admin-login", response_model=TokenResponse)
async def admin_login(
    payload: AdminLoginRequest,
    request: Request,
    response: Response,
    session: AsyncSession = Depends(get_db_session),
) -> TokenResponse:
    result = await service.admin_login(
        session,
        login=payload.login,
        password=payload.password,
        ip_address=request.client.host if request.client else None,
        user_agent=request.headers.get("user-agent"),
    )
    _attach_docs_auth_cookies(request, response, result)
    return result


@router.post("/token", response_model=TokenResponse, include_in_schema=False)
@legacy_router.post("/token", response_model=TokenResponse, include_in_schema=False)
async def token_login(
    request: Request,
    response: Response,
    form_data: OAuth2PasswordRequestForm = Depends(),
    session: AsyncSession = Depends(get_db_session),
) -> TokenResponse:
    result = await service.login(
        session,
        request.app.state.redis,
        email=form_data.username,
        password=form_data.password,
        tenant_id=request.headers.get("X-Tenant-ID"),
        ip_address=request.client.host if request.client else None,
        user_agent=request.headers.get("user-agent"),
    )
    _attach_docs_auth_cookies(request, response, result)
    return result


@router.post("/refresh", response_model=TokenResponse)
@legacy_router.post("/refresh", response_model=TokenResponse)
async def refresh(
    payload: RefreshRequest,
    request: Request,
    response: Response,
    session: AsyncSession = Depends(get_db_session),
) -> TokenResponse:
    result = await service.refresh(
        session,
        payload.refresh_token,
        ip_address=request.client.host if request.client else None,
        user_agent=request.headers.get("user-agent"),
    )
    _attach_docs_auth_cookies(request, response, result)
    return result


@router.post("/logout", response_model=MessageResponse)
@legacy_router.post("/logout", response_model=MessageResponse)
async def logout(
    payload: LogoutRequest,
    response: Response,
    session: AsyncSession = Depends(get_db_session),
) -> MessageResponse:
    result = await service.logout(session, payload.refresh_token)
    response.delete_cookie("neura_access_token")
    response.delete_cookie("neura_refresh_token")
    return result


@router.get("/me", response_model=UserResponse)
@legacy_router.get("/me", response_model=UserResponse)
async def me(
    current_user: User = Depends(get_current_user),
    session: AsyncSession = Depends(get_db_session),
) -> UserResponse:
    return await service.get_profile(session, current_user)


@router.put("/me", response_model=UserResponse)
@legacy_router.put("/me", response_model=UserResponse)
async def update_me(
    payload: UpdateMeRequest,
    current_user: User = Depends(get_current_user),
    session: AsyncSession = Depends(get_db_session),
) -> UserResponse:
    return await service.update_profile(session, current_user, payload)


@router.post("/change-password", response_model=MessageResponse)
@legacy_router.post("/change-password", response_model=MessageResponse)
async def change_password(
    payload: ChangePasswordRequest,
    current_user: User = Depends(get_current_user),
    session: AsyncSession = Depends(get_db_session),
) -> MessageResponse:
    return await service.change_password(session, current_user, payload)


@router.get("/partner/referral", response_model=PartnerReferralResponse)
async def referral(
    current_user: User = Depends(get_current_user),
    session: AsyncSession = Depends(get_db_session),
) -> PartnerReferralResponse:
    return await service.get_partner_referral(session, current_user)


def _attach_docs_auth_cookies(request: Request, response: Response, payload: TokenResponse) -> None:
    if not _should_use_docs_auth_cookies(request):
        return

    response.set_cookie(
        key="neura_access_token",
        value=payload.access_token,
        max_age=payload.expires_in,
        httponly=True,
        samesite="lax",
    )
    response.set_cookie(
        key="neura_refresh_token",
        value=payload.refresh_token,
        max_age=payload.refresh_expires_in,
        httponly=True,
        samesite="lax",
    )


def _should_use_docs_auth_cookies(request: Request) -> bool:
    if settings.app.env != "local":
        return False

    referer = request.headers.get("referer", "")
    return "/docs" in referer or "/redoc" in referer
