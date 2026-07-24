from pydantic import BaseModel, ConfigDict, Field

from backend.app.schemas.auth import UserPublic


class UpdateProfileRequest(BaseModel):
    model_config = ConfigDict(extra="forbid")

    full_name: str | None = Field(default=None, min_length=2, max_length=255)
    phone: str | None = Field(default=None, max_length=32)
    company_name: str | None = Field(default=None, max_length=255)


class ProfileResponse(UserPublic):
    referral_code: str | None = None
