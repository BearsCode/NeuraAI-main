from fastapi import HTTPException, status
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from backend.app.core.security import encrypt_secret
from backend.app.db.enums import IntegrationPlatform, IntegrationStatus
from backend.app.db.social_integration import SocialIntegration
from backend.app.db.user import User
from backend.app.schemas.integrations import (
    IntegrationConnectRequest,
    IntegrationConnectionResponse,
    IntegrationUpdateRequest,
)
from backend.app.services.project_service import ensure_project_access


class IntegrationService:
    async def list_integrations(
        self,
        session: AsyncSession,
        current_user: User,
        project_id: str,
    ) -> list[IntegrationConnectionResponse]:
        project = await ensure_project_access(session, project_id, current_user)
        return [self._to_response(item) for item in project.integrations]

    async def connect(
        self,
        session: AsyncSession,
        current_user: User,
        project_id: str,
        payload: IntegrationConnectRequest,
    ) -> IntegrationConnectionResponse:
        project = await ensure_project_access(session, project_id, current_user)
        platform = IntegrationPlatform(payload.platform)
        integration = await session.scalar(
            select(SocialIntegration).where(
                SocialIntegration.project_id == project_id,
                SocialIntegration.platform == platform,
            )
        )
        if integration:
            integration.account_handle = payload.account_handle
            if payload.access_token:
                integration.encrypted_access_token = encrypt_secret(payload.access_token)
            if payload.refresh_token:
                integration.encrypted_refresh_token = encrypt_secret(payload.refresh_token)
            integration.autoposting_enabled = payload.autoposting_enabled
            integration.publication_settings = payload.publication_settings
            integration.status = IntegrationStatus.CONNECTED
        else:
            integration = SocialIntegration(
                tenant_id=project.tenant_id,
                project_id=project_id,
                platform=platform,
                account_handle=payload.account_handle,
                encrypted_access_token=encrypt_secret(payload.access_token) if payload.access_token else None,
                encrypted_refresh_token=encrypt_secret(payload.refresh_token) if payload.refresh_token else None,
                autoposting_enabled=payload.autoposting_enabled,
                publication_settings=payload.publication_settings,
                status=IntegrationStatus.CONNECTED,
            )
            session.add(integration)

        await session.commit()
        await session.refresh(integration)
        return self._to_response(integration)

    async def update(
        self,
        session: AsyncSession,
        current_user: User,
        project_id: str,
        platform_name: str,
        payload: IntegrationUpdateRequest,
    ) -> IntegrationConnectionResponse:
        await ensure_project_access(session, project_id, current_user)
        platform = IntegrationPlatform(platform_name)
        integration = await session.scalar(
            select(SocialIntegration).where(
                SocialIntegration.project_id == project_id,
                SocialIntegration.platform == platform,
            )
        )
        if not integration:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Integration not found")

        updates = payload.model_dump(exclude_none=True)
        if "status" in updates:
            updates["status"] = IntegrationStatus(updates["status"])
        for field, value in updates.items():
            setattr(integration, field, value)

        await session.commit()
        await session.refresh(integration)
        return self._to_response(integration)

    async def disconnect(
        self,
        session: AsyncSession,
        current_user: User,
        project_id: str,
        platform_name: str,
    ) -> None:
        await ensure_project_access(session, project_id, current_user)
        platform = IntegrationPlatform(platform_name)
        integration = await session.scalar(
            select(SocialIntegration).where(
                SocialIntegration.project_id == project_id,
                SocialIntegration.platform == platform,
            )
        )
        if not integration:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Integration not found")

        integration.status = IntegrationStatus.DISCONNECTED
        integration.autoposting_enabled = False
        await session.commit()

    def _to_response(self, integration: SocialIntegration) -> IntegrationConnectionResponse:
        return IntegrationConnectionResponse(
            integration_id=integration.id,
            project_id=integration.project_id,
            platform=integration.platform.value,
            account_handle=integration.account_handle,
            connected=integration.status == IntegrationStatus.CONNECTED,
            status=integration.status.value,
            autoposting_enabled=integration.autoposting_enabled,
            publication_settings=integration.publication_settings or {},
        )
