from __future__ import annotations

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from backend.app.db.asset import Asset


class FileRepository:
    def __init__(self, session: AsyncSession) -> None:
        self.session = session

    async def create_asset(self, asset: Asset) -> Asset:
        self.session.add(asset)
        await self.session.flush()
        return asset

    async def list_assets(self, tenant_id: str, project_id: str) -> list[Asset]:
        return list(
            (
                await self.session.scalars(
                    select(Asset)
                    .where(Asset.tenant_id == tenant_id, Asset.project_id == project_id)
                    .order_by(Asset.created_at.desc())
                )
            ).all()
        )
