from __future__ import annotations

from pathlib import Path
from uuid import uuid4

import boto3
from sqlalchemy.ext.asyncio import AsyncSession

from backend.app.core.configs import settings
from backend.app.db.asset import Asset
from backend.app.db.enums import AssetType
from backend.app.db.user import User
from backend.app.modules.access import ensure_project_access
from backend.app.modules.files.repository import FileRepository
from backend.app.modules.files.schemas import (
    CompleteUploadRequest,
    FileAssetResponse,
    UploadUrlResponse,
)


class FileService:
    async def create_upload_url(
        self,
        session: AsyncSession,
        current_user: User,
        tenant_id: str,
        project_id: str,
        file_name: str,
        content_type: str,
    ) -> UploadUrlResponse:
        await ensure_project_access(session, current_user, tenant_id, project_id)
        object_key = f"{tenant_id}/{project_id}/{uuid4().hex}_{file_name}"
        if settings.s3.endpoint_url:
            client = boto3.client(
                "s3",
                endpoint_url=settings.s3.endpoint_url,
                aws_access_key_id=settings.s3.access_key_id.get_secret_value() if settings.s3.access_key_id else None,
                aws_secret_access_key=settings.s3.secret_access_key.get_secret_value() if settings.s3.secret_access_key else None,
                region_name=settings.s3.region,
            )
            upload_url = client.generate_presigned_url(
                "put_object",
                Params={
                    "Bucket": settings.s3.bucket,
                    "Key": object_key,
                    "ContentType": content_type,
                },
                ExpiresIn=settings.s3.signed_url_ttl_seconds,
            )
        else:
            Path(settings.s3.local_root).mkdir(parents=True, exist_ok=True)
            upload_url = f"file://{settings.s3.local_root}/{object_key}"

        return UploadUrlResponse(
            object_key=object_key,
            upload_url=upload_url,
            expires_in=settings.s3.signed_url_ttl_seconds,
        )

    async def complete_upload(
        self,
        session: AsyncSession,
        current_user: User,
        tenant_id: str,
        project_id: str,
        payload: CompleteUploadRequest,
    ) -> FileAssetResponse:
        await ensure_project_access(session, current_user, tenant_id, project_id)
        repository = FileRepository(session)
        public_url = (
            f"{settings.s3.public_base_url.rstrip('/')}/{payload.object_key}"
            if settings.s3.public_base_url
            else None
        )
        asset = await repository.create_asset(
            Asset(
                tenant_id=tenant_id,
                project_id=project_id,
                asset_type=AssetType(payload.asset_type),
                file_name=payload.file_name,
                content_type=payload.content_type,
                storage_uri=f"s3://{settings.s3.bucket}/{payload.object_key}",
                public_url=public_url,
                size_bytes=payload.size_bytes,
                checksum_sha256=payload.checksum_sha256,
            )
        )
        await session.commit()
        return self._to_response(asset)

    async def list_assets(
        self,
        session: AsyncSession,
        current_user: User,
        tenant_id: str,
        project_id: str,
    ) -> list[FileAssetResponse]:
        await ensure_project_access(session, current_user, tenant_id, project_id)
        assets = await FileRepository(session).list_assets(tenant_id, project_id)
        return [self._to_response(asset) for asset in assets]

    def _to_response(self, asset: Asset) -> FileAssetResponse:
        return FileAssetResponse(
            asset_id=asset.id,
            tenant_id=asset.tenant_id,
            project_id=asset.project_id,
            file_name=asset.file_name,
            content_type=asset.content_type,
            asset_type=asset.asset_type.value,
            storage_uri=asset.storage_uri,
            public_url=asset.public_url,
            size_bytes=asset.size_bytes,
            created_at=asset.created_at,
        )
