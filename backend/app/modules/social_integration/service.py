from __future__ import annotations

from fastapi import HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession

from backend.app.core.configs import settings
from backend.app.core.security import encrypt_secret
from backend.app.db.enums import IntegrationPlatform, IntegrationStatus
from backend.app.db.social_integration import SocialIntegration
from backend.app.db.user import User
from backend.app.integrations.social_adapters import SocialAdapterRegistry
from backend.app.integrations.social_clients import SocialClientRegistry
from backend.app.modules.access import ensure_project_access
from backend.app.modules.social_integration.repository import SocialIntegrationRepository
from backend.app.modules.social_integration.schemas import (
    SocialAuthorizeResponse,
    SocialConnectRequest,
    SocialConnectionResponse,
    SocialOAuthCallbackRequest,
    SocialUpdateRequest,
)


class SocialIntegrationService:
    """Application service for Telegram/VK connections."""

    async def list_connections(
        self,
        session: AsyncSession,
        current_user: User,
        tenant_id: str,
        project_id: str,
    ) -> list[SocialConnectionResponse]:
        await ensure_project_access(session, current_user, tenant_id, project_id)
        integrations = await SocialIntegrationRepository(session).list_for_project(tenant_id, project_id)
        return [self._to_response(item) for item in integrations]

    async def begin_authorization(
        self,
        session: AsyncSession,
        current_user: User,
        tenant_id: str,
        project_id: str,
        platform: str,
        redirect_uri: str,
    ) -> SocialAuthorizeResponse:
        """Return an auth URL for a provider."""

        await ensure_project_access(session, current_user, tenant_id, project_id)
        auth_start = await SocialClientRegistry().client_for(platform).auth(redirect_uri)
        return SocialAuthorizeResponse(
            authorization_url=auth_start.authorization_url,
            state=auth_start.state,
            code_verifier=auth_start.code_verifier,
        )

    async def complete_authorization(
        self,
        session: AsyncSession,
        current_user: User,
        tenant_id: str,
        project_id: str,
        platform: str,
        payload: SocialOAuthCallbackRequest,
    ) -> SocialConnectionResponse:
        """Exchange provider auth data and persist the integration."""

        await ensure_project_access(session, current_user, tenant_id, project_id)
        client = SocialClientRegistry().client_for(platform)
        auth_result = await client.callback(
            payload.code,
            payload.redirect_uri,
            code_verifier=payload.code_verifier,
            account_hint=payload.account_handle,
        )
        repository = SocialIntegrationRepository(session)
        integration = await repository.get_for_project_platform(tenant_id, project_id, platform)
        publication_settings = {
            **payload.publication_settings,
            "auth_metadata": auth_result.metadata,
        }
        if integration:
            integration.account_handle = auth_result.account_handle
            integration.encrypted_access_token = encrypt_secret(auth_result.access_token)
            integration.encrypted_refresh_token = (
                encrypt_secret(auth_result.refresh_token) if auth_result.refresh_token else None
            )
            integration.token_expires_at = auth_result.expires_at
            integration.autoposting_enabled = payload.autoposting_enabled
            integration.publication_settings = publication_settings
            integration.scopes = auth_result.scopes
            integration.status = IntegrationStatus.CONNECTED
        else:
            integration = await repository.create(
                SocialIntegration(
                    tenant_id=tenant_id,
                    project_id=project_id,
                    platform=IntegrationPlatform(platform),
                    account_handle=auth_result.account_handle,
                    status=IntegrationStatus.CONNECTED,
                    encrypted_access_token=encrypt_secret(auth_result.access_token),
                    encrypted_refresh_token=(
                        encrypt_secret(auth_result.refresh_token) if auth_result.refresh_token else None
                    ),
                    token_expires_at=auth_result.expires_at,
                    autoposting_enabled=payload.autoposting_enabled,
                    publication_settings=publication_settings,
                    scopes=auth_result.scopes,
                )
            )
        await session.commit()
        return self._to_response(integration)

    async def connect(
        self,
        session: AsyncSession,
        current_user: User,
        tenant_id: str,
        project_id: str,
        payload: SocialConnectRequest,
    ) -> SocialConnectionResponse:
        await ensure_project_access(session, current_user, tenant_id, project_id)
        await self._validate_credentials(payload.platform, payload.account_handle, payload.access_token)
        repository = SocialIntegrationRepository(session)
        integration = await repository.get_for_project_platform(
            tenant_id,
            project_id,
            payload.platform,
        )
        if integration:
            integration.account_handle = payload.account_handle
            integration.encrypted_access_token = encrypt_secret(payload.access_token)
            integration.encrypted_refresh_token = encrypt_secret(payload.refresh_token) if payload.refresh_token else None
            integration.autoposting_enabled = payload.autoposting_enabled
            integration.publication_settings = payload.publication_settings
            integration.scopes = payload.scopes
            integration.status = IntegrationStatus.CONNECTED
        else:
            integration = await repository.create(
                SocialIntegration(
                    tenant_id=tenant_id,
                    project_id=project_id,
                    platform=IntegrationPlatform(payload.platform),
                    account_handle=payload.account_handle,
                    status=IntegrationStatus.CONNECTED,
                    encrypted_access_token=encrypt_secret(payload.access_token),
                    encrypted_refresh_token=encrypt_secret(payload.refresh_token) if payload.refresh_token else None,
                    autoposting_enabled=payload.autoposting_enabled,
                    publication_settings=payload.publication_settings,
                    scopes=payload.scopes,
                )
            )
        await session.commit()
        return self._to_response(integration)

    async def update(
        self,
        session: AsyncSession,
        current_user: User,
        tenant_id: str,
        project_id: str,
        platform: str,
        payload: SocialUpdateRequest,
    ) -> SocialConnectionResponse:
        await ensure_project_access(session, current_user, tenant_id, project_id)
        repository = SocialIntegrationRepository(session)
        integration = await repository.get_for_project_platform(tenant_id, project_id, platform)
        if not integration:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Integration not found")

        if payload.autoposting_enabled is not None:
            integration.autoposting_enabled = payload.autoposting_enabled
        if payload.publication_settings is not None:
            integration.publication_settings = payload.publication_settings
        if payload.access_token:
            integration.encrypted_access_token = encrypt_secret(payload.access_token)
        if payload.refresh_token:
            integration.encrypted_refresh_token = encrypt_secret(payload.refresh_token)
        await session.commit()
        return self._to_response(integration)

    async def disconnect(
        self,
        session: AsyncSession,
        current_user: User,
        tenant_id: str,
        project_id: str,
        platform: str,
    ) -> SocialConnectionResponse:
        await ensure_project_access(session, current_user, tenant_id, project_id)
        repository = SocialIntegrationRepository(session)
        integration = await repository.get_for_project_platform(tenant_id, project_id, platform)
        if not integration:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Integration not found")
        integration.status = IntegrationStatus.DISCONNECTED
        integration.autoposting_enabled = False
        await session.commit()
        return self._to_response(integration)

    async def _validate_credentials(self, platform: str, account_handle: str, access_token: str) -> None:
        if settings.social.mode != "live":
            return
        try:
            await SocialAdapterRegistry().adapter_for(platform).validate_connection(account_handle, access_token)
        except NotImplementedError as exc:
            raise HTTPException(status_code=status.HTTP_501_NOT_IMPLEMENTED, detail=str(exc)) from exc
        except Exception as exc:
            raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(exc)) from exc

    def _to_response(self, integration: SocialIntegration) -> SocialConnectionResponse:
        return SocialConnectionResponse(
            integration_id=integration.id,
            project_id=integration.project_id,
            tenant_id=integration.tenant_id,
            platform=integration.platform.value,
            account_handle=integration.account_handle,
            status=integration.status.value,
            autoposting_enabled=integration.autoposting_enabled,
            scopes=integration.scopes,
            publication_settings=integration.publication_settings,
            created_at=integration.created_at,
        )
