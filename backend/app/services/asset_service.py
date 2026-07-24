from fastapi import UploadFile
from sqlalchemy.ext.asyncio import AsyncSession

from backend.app.db.asset import Asset
from backend.app.db.enums import AssetType
from backend.app.db.user import User
from backend.app.integrations.storage_client import StorageClient
from backend.app.schemas.assets import AssetResponse
from backend.app.services.project_service import ensure_project_access


class AssetService:
    async def list_assets(
        self,
        session: AsyncSession,
        current_user: User,
        project_id: str,
    ) -> list[AssetResponse]:
        project = await ensure_project_access(session, project_id, current_user)
        return [self._to_response(asset) for asset in project.assets]

    async def upload_asset(
        self,
        session: AsyncSession,
        current_user: User,
        project_id: str,
        asset_type: AssetType,
        file: UploadFile,
        storage_client: StorageClient,
    ) -> AssetResponse:
        project = await ensure_project_access(session, project_id, current_user)
        storage_uri, public_url = await storage_client.store_upload(project.id, file)
        asset = Asset(
            project_id=project.id,
            asset_type=asset_type,
            file_name=file.filename or "upload.bin",
            content_type=file.content_type or "application/octet-stream",
            storage_uri=storage_uri,
            public_url=public_url,
        )
        session.add(asset)
        await session.commit()
        await session.refresh(asset)
        return self._to_response(asset)

    def _to_response(self, asset: Asset) -> AssetResponse:
        return AssetResponse(
            asset_id=asset.id,
            project_id=asset.project_id,
            asset_type=asset.asset_type.value,
            file_name=asset.file_name,
            content_type=asset.content_type,
            storage_uri=asset.storage_uri,
            public_url=asset.public_url,
            created_at=asset.created_at,
        )
