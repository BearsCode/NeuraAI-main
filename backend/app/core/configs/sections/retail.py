from __future__ import annotations

from pydantic import Field, SecretStr

from backend.app.core.configs.base import ConfigSection


class RetailConfig(ConfigSection):
    c1_enabled: bool = Field(default=False, alias="RETAIL__C1_ENABLED")
    c1_base_url: str = Field(default="", alias="RETAIL__C1_BASE_URL")
    c1_login: str = Field(default="", alias="RETAIL__C1_LOGIN")
    c1_password: SecretStr = Field(default=SecretStr(""), alias="RETAIL__C1_PASSWORD")

    moysklad_enabled: bool = Field(default=False, alias="RETAIL__MOYSKLAD_ENABLED")
    moysklad_token: SecretStr = Field(default=SecretStr(""), alias="RETAIL__MOYSKLAD_TOKEN")
    moysklad_company_id: str = Field(default="", alias="RETAIL__MOYSKLAD_COMPANY_ID")


def get_retail_config() -> RetailConfig:
    return RetailConfig()
