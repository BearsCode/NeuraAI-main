from __future__ import annotations


from sqlalchemy import desc, select
from sqlalchemy.ext.asyncio import AsyncSession

from backend.app.core.configs import settings
from backend.app.db.avatar import Avatar
from backend.app.db.avatar_training_job import AvatarTrainingJob
from backend.app.db.enums import AvatarStatus, AvatarType
from backend.app.integrations import ai_client, storage_client


class AvatarService:
    async def create_photo_avatar(
        self, session: AsyncSession, tenant_id: str, photo_urls: list[str]
    ) -> dict:
        avatar = Avatar(
            tenant_id=tenant_id,
            avatar_type=AvatarType.PHOTO.value,
            status=AvatarStatus.TRAINING.value,
            source_urls=photo_urls,
            provider="replicate",
            config={
                "model": "stable-diffusion",
                "method": "lora",
                "training_steps": 1000,
            },
        )
        session.add(avatar)
        await session.flush()

        job = AvatarTrainingJob(
            tenant_id=tenant_id,
            avatar_id=avatar.id,
            avatar_type=AvatarType.PHOTO.value,
            status="pending",
            provider="replicate",
            input_data={"source_urls": photo_urls, "method": "lora"},
        )
        session.add(job)

        if settings.avatar.replicate.api_key:
            try:
                lora_version = await ai_client.train_lora(
                    image_urls=photo_urls,
                    trigger_word=avatar.id[:8],
                )
                avatar.model_weights_url = lora_version
                avatar.status = AvatarStatus.READY.value
                job.status = "completed"
                job.output_data = {"lora_version": lora_version}
            except Exception as exc:
                avatar.status = AvatarStatus.FAILED.value
                job.status = "failed"
                job.error = str(exc)
        else:
            job.status = "completed"
            avatar.status = AvatarStatus.READY.value

        await session.commit()

        return {
            "avatar_id": avatar.id,
            "type": "photo",
            "status": avatar.status,
            "job_id": job.id,
            "estimated_time_minutes": 20,
            "source_urls": photo_urls,
        }

    async def create_video_avatar(
        self, session: AsyncSession, tenant_id: str, video_url: str
    ) -> dict:
        avatar = Avatar(
            tenant_id=tenant_id,
            avatar_type=AvatarType.VIDEO.value,
            status=AvatarStatus.TRAINING.value,
            source_urls=[video_url],
            provider="heygen",
            config={
                "primary_provider": "heygen",
                "fallback_provider": "d-id",
            },
        )
        session.add(avatar)
        await session.flush()

        job = AvatarTrainingJob(
            tenant_id=tenant_id,
            avatar_id=avatar.id,
            avatar_type=AvatarType.VIDEO.value,
            status="pending",
            provider="heygen",
            input_data={"video_url": video_url},
        )
        session.add(job)

        if settings.avatar.heygen.api_key:
            try:
                heygen_cfg = settings.avatar.heygen
                headers = {
                    "X-Api-Key": heygen_cfg.api_key.get_secret_value(),
                    "Content-Type": "application/json",
                }
                import httpx
                async with httpx.AsyncClient(timeout=30.0) as client:
                    create_response = await client.post(
                        f"{heygen_cfg.base_url}/v2/avatars",
                        headers=headers,
                        json={
                            "avatar_name": f"neuara_{tenant_id[:8]}",
                            "video_url": video_url,
                            "source_type": "video",
                        },
                    )
                    if create_response.status_code == 200:
                        avatar_data = create_response.json().get("data", {})
                        heygen_id = avatar_data.get("avatar_id", "")
                        avatar.preview_url = avatar_data.get("preview_url", "")
                        avatar.model_weights_url = heygen_id
                        job.status = "completed"
                        job.output_data = {"heygen_avatar_id": heygen_id}
                        avatar.status = AvatarStatus.READY.value
                    else:
                        error_detail = create_response.text
                        job.status = "failed"
                        job.error = f"HeyGen avatar creation failed: {error_detail}"
                        avatar.status = AvatarStatus.FAILED.value
            except Exception as exc:
                avatar.status = AvatarStatus.FAILED.value
                job.status = "failed"
                job.error = str(exc)
        else:
            job.status = "completed"
            avatar.status = AvatarStatus.READY.value

        await session.commit()

        return {
            "avatar_id": avatar.id,
            "type": "video",
            "status": avatar.status,
            "job_id": job.id,
            "estimated_time_minutes": 15,
            "source_video": video_url,
        }

    async def get_avatar(
        self, session: AsyncSession, tenant_id: str, avatar_id: str
    ) -> dict | None:
        avatar = await session.scalar(
            select(Avatar).where(Avatar.id == avatar_id, Avatar.tenant_id == tenant_id)
        )
        if not avatar:
            return None

        return {
            "id": avatar.id,
            "type": avatar.avatar_type,
            "status": avatar.status,
            "preview_url": avatar.preview_url,
            "is_active": avatar.is_active,
            "provider": avatar.provider,
            "created_at": avatar.created_at.isoformat(),
        }

    async def list_avatars(
        self, session: AsyncSession, tenant_id: str
    ) -> list[dict]:
        avatars = (
            await session.scalars(
                select(Avatar)
                .where(Avatar.tenant_id == tenant_id)
                .order_by(desc(Avatar.created_at))
            )
        ).all()

        return [
            {
                "id": a.id,
                "type": a.avatar_type,
                "status": a.status,
                "preview_url": a.preview_url,
                "is_active": a.is_active,
                "provider": a.provider,
                "created_at": a.created_at.isoformat(),
            }
            for a in avatars
        ]

    async def delete_avatar(
        self, session: AsyncSession, tenant_id: str, avatar_id: str
    ) -> dict:
        avatar = await session.scalar(
            select(Avatar).where(Avatar.id == avatar_id, Avatar.tenant_id == tenant_id)
        )
        if not avatar:
            return {"deleted": False, "error": "Avatar not found"}

        if avatar.model_weights_url:
            await storage_client.delete(avatar.model_weights_url)

        await session.delete(avatar)
        await session.commit()
        return {"deleted": True, "avatar_id": avatar_id}

    async def get_training_status(
        self, session: AsyncSession, tenant_id: str, avatar_id: str
    ) -> dict:
        avatar = await session.scalar(
            select(Avatar).where(Avatar.id == avatar_id, Avatar.tenant_id == tenant_id)
        )

        jobs = (
            await session.scalars(
                select(AvatarTrainingJob)
                .where(
                    AvatarTrainingJob.avatar_id == avatar_id,
                    AvatarTrainingJob.tenant_id == tenant_id,
                )
                .order_by(desc(AvatarTrainingJob.created_at))
                .limit(1)
            )
        ).first()

        return {
            "avatar_id": avatar_id,
            "avatar_status": avatar.status if avatar else "unknown",
            "job_status": jobs.status if jobs else "no_jobs",
            "job_error": jobs.error if jobs else None,
        }
