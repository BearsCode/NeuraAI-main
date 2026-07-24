import re

from pydantic import BaseModel, ConfigDict, EmailStr, field_validator

from backend.app.core.configs import settings


class RegisterRequest(BaseModel):
    model_config = ConfigDict(extra="forbid")

    email: EmailStr
    password: str
    full_name: str
    phone: str | None = None
    company_name: str | None = None
    referral_code: str | None = None

    @field_validator("password")
    @classmethod
    def validate_password(cls, v: str) -> str:
        pw = settings.password
        min_len = pw.min_length
        if len(v) < min_len:
            raise ValueError(f"Password must be at least {min_len} characters")
        if pw.require_uppercase and not re.search(r"[A-Z]", v):
            raise ValueError("Password must contain at least one uppercase letter")
        if pw.require_lowercase and not re.search(r"[a-z]", v):
            raise ValueError("Password must contain at least one lowercase letter")
        if pw.require_digit and not re.search(r"\d", v):
            raise ValueError("Password must contain at least one digit")
        if pw.require_special and not re.search(r"[!@#$%^&*(),.?\":{}|<>_\-+]", v):
            raise ValueError("Password must contain at least one special character")
        return v


class LoginRequest(BaseModel):
    model_config = ConfigDict(extra="forbid")


    email: EmailStr
    password: str


class UserPublic(BaseModel):
    user_id: str
    email: EmailStr
    full_name: str
    phone: str | None = None
    company_name: str | None = None
    role: str
    admin_role: str | None = None
    is_active: bool


class RefreshTokenRequest(BaseModel):
    model_config = ConfigDict(extra="forbid")

    refresh_token: str


class LogoutRequest(BaseModel):
    model_config = ConfigDict(extra="forbid")

    refresh_token: str


class MessageResponse(BaseModel):
    message: str


class TokenResponse(BaseModel):
    access_token: str
    refresh_token: str
    token_type: str = "bearer"
    expires_in: int
    refresh_expires_in: int
    user: UserPublic
