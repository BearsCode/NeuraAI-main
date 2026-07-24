from __future__ import annotations

from datetime import datetime

from pydantic import BaseModel, ConfigDict, EmailStr, Field


class RegisterRequest(BaseModel):
    """Create a new account and start email verification."""

    model_config = ConfigDict(extra="forbid")

    email: EmailStr
    password: str = Field(min_length=8)
    full_name: str = Field(min_length=2, max_length=255)
    company_name: str | None = Field(default=None, max_length=255)
    phone: str | None = Field(default=None, max_length=32)
    referral_code: str | None = None


class RegistrationAcceptedResponse(BaseModel):
    """Confirmation sent to the user email."""

    message: str
    email: EmailStr
    verification_required: bool = True
    verification_ttl_seconds: int
    debug_code: str | None = None


class VerifyEmailRequest(BaseModel):
    """Verify ownership of the email using an OTP code."""

    model_config = ConfigDict(extra="forbid")

    email: EmailStr
    code: str = Field(min_length=4, max_length=12)


class ResendVerificationRequest(BaseModel):
    """Request a new verification code for a pending account."""

    model_config = ConfigDict(extra="forbid")

    email: EmailStr


class LoginRequest(BaseModel):
    """User login payload."""

    model_config = ConfigDict(extra="forbid")

    email: EmailStr
    password: str
    tenant_id: str | None = None


class AdminLoginRequest(BaseModel):
    """Admin login payload (login + password, not email)."""

    model_config = ConfigDict(extra="forbid")

    login: str
    password: str


class RefreshRequest(BaseModel):
    """Refresh access and refresh tokens."""

    model_config = ConfigDict(extra="forbid")

    refresh_token: str


class LogoutRequest(BaseModel):
    """Invalidate a refresh token session."""

    model_config = ConfigDict(extra="forbid")

    refresh_token: str


class UpdateMeRequest(BaseModel):
    """Patch profile fields for the authenticated user."""

    model_config = ConfigDict(extra="forbid")

    full_name: str | None = Field(default=None, min_length=2, max_length=255)
    phone: str | None = Field(default=None, max_length=32)


class ChangePasswordRequest(BaseModel):
    """Change password for the authenticated user."""

    model_config = ConfigDict(extra="forbid")

    current_password: str
    new_password: str = Field(min_length=8)


class MembershipResponse(BaseModel):
    """Tenant membership visible in the user profile."""

    tenant_id: str
    tenant_name: str
    tenant_slug: str
    role: str
    is_primary: bool


class UserResponse(BaseModel):
    """Authenticated user profile payload."""

    user_id: str
    email: EmailStr
    full_name: str
    phone: str | None
    role: str
    admin_role: str | None = None
    is_active: bool
    is_verified: bool
    memberships: list[MembershipResponse] = Field(default_factory=list)


class TokenResponse(BaseModel):
    """Access and refresh tokens returned by auth flows."""

    access_token: str
    refresh_token: str
    token_type: str = "bearer"
    expires_in: int
    refresh_expires_in: int
    user: UserResponse


class PartnerReferralResponse(BaseModel):
    """Referral snapshot for partners."""

    referral_code: str
    referral_link: str
    commission_rate: float
    total_income: float
    pending_payout: float


class VKCallbackRequest(BaseModel):
    """VK authorization code from redirect OAuth flow."""

    model_config = ConfigDict(extra="forbid")

    code: str
    redirect_uri: str


class YandexCallbackRequest(BaseModel):
    """Yandex authorization code from redirect OAuth flow."""

    model_config = ConfigDict(extra="forbid")

    code: str
    redirect_uri: str


class MailruCallbackRequest(BaseModel):
    """Mail.ru authorization code from redirect OAuth flow."""

    model_config = ConfigDict(extra="forbid")

    code: str
    redirect_uri: str


class TelegramLoginRequest(BaseModel):
    """Telegram Login widget data (initData fields)."""

    model_config = ConfigDict(extra="forbid")

    id: int
    first_name: str
    last_name: str | None = None
    username: str | None = None
    photo_url: str | None = None
    auth_date: int
    hash: str


class MessageResponse(BaseModel):
    """Simple timestamped message envelope."""

    message: str
    timestamp: datetime
