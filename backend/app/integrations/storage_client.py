from __future__ import annotations

import asyncio
import mimetypes
from pathlib import Path
from uuid import uuid4

import httpx
import boto3
from fastapi import HTTPException, UploadFile, status

from backend.app.core.configs import settings


def _sanitize_path_component(component: str) -> str:
    """Remove path traversal sequences from a single path component."""
    cleaned = component.replace("..", "").replace("/", "").replace("\\", "")
    return cleaned or "_"

try:
    import aioboto3
except ImportError:  # pragma: no cover - local env may not be reinstalled yet
    aioboto3 = None


class StorageClient:
    async def initialize(self) -> None:
        if settings.storage_backend == "local":
            Path(settings.local_storage_path).mkdir(parents=True, exist_ok=True)

    async def store_upload(self, project_id: str, file: UploadFile) -> tuple[str, str | None]:
        self._validate_upload(file)

        suffix = Path(file.filename or "upload.bin").suffix
        file_name = f"{uuid4().hex}{suffix}"

        if settings.storage_backend == "s3":
            return await self._store_in_s3(project_id, file_name, file)

        return await self._store_locally(project_id, file_name, file)

    async def healthcheck(self) -> dict[str, str]:
        if settings.storage_backend == "local":
            try:
                Path(settings.local_storage_path).mkdir(parents=True, exist_ok=True)
                return {
                    "status": "ok",
                    "backend": "local",
                    "path": settings.local_storage_path,
                }
            except Exception as exc:
                return {
                    "status": "down",
                    "backend": "local",
                    "detail": str(exc),
                }

        try:
            client = self._build_s3_client()
            await asyncio.to_thread(client.head_bucket, Bucket=settings.s3_bucket_name)
            return {
                "status": "ok",
                "backend": "s3",
                "bucket": settings.s3_bucket_name,
            }
        except Exception as exc:
            return {
                "status": "down",
                "backend": "s3",
                "detail": str(exc),
            }

    async def upload_from_url(self, url: str, prefix: str = "") -> str:
        safe_prefix = _sanitize_path_component(prefix)
        if safe_prefix:
            safe_prefix += "/"
        async with httpx.AsyncClient(timeout=60.0) as client:
            response = await client.get(url)
            response.raise_for_status()
            data = response.content

        content_type = response.headers.get("content-type", "application/octet-stream")
        ext = mimetypes.guess_extension(content_type) or ".bin"
        file_name = f"{uuid4().hex}{ext}"
        object_key = f"{safe_prefix}{file_name}"

        if settings.storage_backend == "s3":
            s3_client = self._build_s3_client()
            await asyncio.to_thread(
                s3_client.put_object,
                Bucket=settings.s3_bucket_name,
                Key=object_key,
                Body=data,
                ContentType=content_type,
            )
            public_url = f"{settings.s3_public_base_url.rstrip('/')}/{object_key}" if settings.s3_public_base_url else object_key
            return public_url

        base_path = Path(settings.local_storage_path)
        dest = base_path / object_key
        dest.parent.mkdir(parents=True, exist_ok=True)
        dest.write_bytes(data)
        return f"{settings.public_base_url.rstrip('/')}/storage/{object_key}"

    async def delete(self, url: str) -> bool:
        if url.startswith("s3://"):
            parts = url.replace("s3://", "").split("/", 1)
            bucket = parts[0] if len(parts) > 1 else settings.s3_bucket_name
            key = parts[1] if len(parts) > 1 else parts[0]
            s3_client = self._build_s3_client()
            try:
                await asyncio.to_thread(s3_client.delete_object, Bucket=bucket, Key=key)
                return True
            except Exception:
                return False

        if url.startswith(settings.public_base_url or "http"):
            path_part = url.replace(settings.public_base_url.rstrip("/") + "/storage/", "") if settings.public_base_url else url
            local_path = Path(settings.local_storage_path) / path_part
            local_path = local_path.resolve()
            if not str(local_path).startswith(str(Path(settings.local_storage_path).resolve())):
                raise HTTPException(status_code=400, detail="Invalid storage path")
            if local_path.exists():
                local_path.unlink()
                return True
        return False

    async def _store_locally(
        self,
        project_id: str,
        file_name: str,
        file: UploadFile,
    ) -> tuple[str, str | None]:
        safe_project_id = _sanitize_path_component(project_id)
        base_path = Path(settings.local_storage_path) / safe_project_id
        base_path.mkdir(parents=True, exist_ok=True)
        destination = base_path / file_name

        total_bytes = 0
        with destination.open("wb") as output:
            while chunk := await file.read(1024 * 1024):
                total_bytes += len(chunk)
                if total_bytes > settings.max_upload_size_bytes:
                    destination.unlink(missing_ok=True)
                    raise HTTPException(
                        status_code=status.HTTP_413_REQUEST_ENTITY_TOO_LARGE,
                        detail=f"File exceeds the {settings.max_upload_size_mb}MB limit",
                    )
                output.write(chunk)

        public_url = (
            f"{settings.public_base_url.rstrip('/')}/storage/{project_id}/{file_name}"
        )
        return str(destination), public_url

    async def _store_in_s3(
        self,
        project_id: str,
        file_name: str,
        file: UploadFile,
    ) -> tuple[str, str | None]:
        payload = await self._read_limited_bytes(file)
        object_key = f"{project_id}/{file_name}"
        if aioboto3 is not None:
            session = aioboto3.Session()
            async with session.client(
                "s3",
                endpoint_url=settings.s3_endpoint_url or None,
                region_name=settings.s3_region,
                aws_access_key_id=settings.s3_access_key or None,
                aws_secret_access_key=settings.s3_secret_key or None,
            ) as client:
                await client.put_object(
                    Bucket=settings.s3_bucket_name,
                    Key=object_key,
                    Body=payload,
                    ContentType=file.content_type or "application/octet-stream",
                )
            return self._s3_result(object_key)

        client = self._build_s3_client()

        await asyncio.to_thread(
            client.put_object,
            Bucket=settings.s3_bucket_name,
            Key=object_key,
            Body=payload,
            ContentType=file.content_type or "application/octet-stream",
        )

        return self._s3_result(object_key)

    async def _read_limited_bytes(self, file: UploadFile) -> bytes:
        total_bytes = 0
        chunks: list[bytes] = []

        while chunk := await file.read(1024 * 1024):
            total_bytes += len(chunk)
            if total_bytes > settings.max_upload_size_bytes:
                raise HTTPException(
                    status_code=status.HTTP_413_REQUEST_ENTITY_TOO_LARGE,
                    detail=f"File exceeds the {settings.max_upload_size_mb}MB limit",
                )
            chunks.append(chunk)

        return b"".join(chunks)

    def _validate_upload(self, file: UploadFile) -> None:
        if not file.filename:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Uploaded file must have a name",
            )

        if (
            settings.allowed_upload_content_types
            and file.content_type not in settings.allowed_upload_content_types
        ):
            raise HTTPException(
                status_code=status.HTTP_415_UNSUPPORTED_MEDIA_TYPE,
                detail="Unsupported file content type",
            )

    def _build_s3_client(self):
        return boto3.client(
            "s3",
            endpoint_url=settings.s3_endpoint_url or None,
            region_name=settings.s3_region,
            aws_access_key_id=settings.s3_access_key or None,
            aws_secret_access_key=settings.s3_secret_key or None,
        )

    def _s3_result(self, object_key: str) -> tuple[str, str | None]:
        public_url = None
        if settings.s3_public_base_url:
            public_url = f"{settings.s3_public_base_url.rstrip('/')}/{object_key}"

        return f"s3://{settings.s3_bucket_name}/{object_key}", public_url

    async def store_bytes(
        self,
        project_id: str,
        file_name: str,
        content_type: str,
        data: bytes,
    ) -> tuple[str, str | None]:
        if len(data) > settings.max_upload_size_bytes:
            raise HTTPException(
                status_code=status.HTTP_413_REQUEST_ENTITY_TOO_LARGE,
                detail=f"File exceeds the {settings.max_upload_size_mb}MB limit",
            )

        safe_project_id = _sanitize_path_component(project_id)

        if settings.storage_backend == "s3":
            object_key = f"{safe_project_id}/{file_name}"
            client = self._build_s3_client()
            await asyncio.to_thread(
                client.put_object,
                Bucket=settings.s3_bucket_name,
                Key=object_key,
                Body=data,
                ContentType=content_type,
            )
            return self._s3_result(object_key)

        base_path = Path(settings.local_storage_path) / safe_project_id
        base_path.mkdir(parents=True, exist_ok=True)
        destination = base_path / file_name
        with destination.open("wb") as output:
            output.write(data)
        public_url = f"{settings.public_base_url.rstrip('/')}/storage/{safe_project_id}/{file_name}"
        return str(destination), public_url
