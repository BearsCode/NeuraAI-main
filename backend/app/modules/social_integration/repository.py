from __future__ import annotations

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from backend.app.db.social_integration import SocialIntegration


class SocialIntegrationRepository:
    def __init__(self, session: AsyncSession) -> None:
        self.session = session

    async def list_for_project(self, tenant_id: str, project_id: str) -> list[SocialIntegration]:
        return list(
            (
                await self.session.scalars(
                    select(SocialIntegration)
                    .where(
                        SocialIntegration.tenant_id == tenant_id,
                        SocialIntegration.project_id == project_id,
                    )
                    .order_by(SocialIntegration.created_at.desc())
                )
            ).all()
        )

    async def get_for_project_platform(
        self,
        tenant_id: str,
        project_id: str,
        platform: str,
    ) -> SocialIntegration | None:
        return await self.session.scalar(
            select(SocialIntegration).where(
                SocialIntegration.tenant_id == tenant_id,
                SocialIntegration.project_id == project_id,
                SocialIntegration.platform == platform,
            )
        )

    async def create(self, integration: SocialIntegration) -> SocialIntegration:
        self.session.add(integration)
        await self.session.flush()
        return integration

    async def get_by_id(self, tenant_id: str, integration_id: str) -> SocialIntegration | None:
        return await self.session.scalar(
            select(SocialIntegration).where(
                SocialIntegration.tenant_id == tenant_id,
                SocialIntegration.id == integration_id,
            )
        )
