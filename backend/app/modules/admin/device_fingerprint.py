from __future__ import annotations

from datetime import UTC, datetime

from fastapi import HTTPException, Request, status
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from backend.app.db.user import User


async def verify_device_fingerprint(
    request: Request,
    user: User,
    session: AsyncSession,
) -> None:
    fingerprint = request.headers.get("X-Device-Fingerprint")
    if not fingerprint:
        return

    from backend.app.db.models import DeviceFingerprint as DeviceFingerprintModel

    result = await session.execute(
        select(DeviceFingerprintModel).where(
            DeviceFingerprintModel.user_id == user.id,
            DeviceFingerprintModel.fingerprint_hash == fingerprint,
            DeviceFingerprintModel.is_trusted.is_(True),
        )
    )
    existing = result.scalar_one_or_none()

    if existing is None:
        if await _is_new_device_confirmation_needed(request, user, session, fingerprint):
            raise HTTPException(
                status_code=status.HTTP_428_PRECONDITION_REQUIRED,
                detail="New device requires confirmation. Check your email.",
            )


async def _is_new_device_confirmation_needed(
    request: Request,
    user: User,
    session: AsyncSession,
    fingerprint: str,
) -> bool:
    if not request.app.state.redis:
        return False

    confirm_key = f"device:confirm:{user.id}:{fingerprint}"
    confirmed = await request.app.state.redis.get(confirm_key)
    if confirmed:
        return False

    from backend.app.db.models import DeviceFingerprint as DeviceFingerprintModel

    new_device = DeviceFingerprintModel(
        user_id=user.id,
        fingerprint_hash=fingerprint,
        device_info=request.headers.get("User-Agent", ""),
        ip_address=request.client.host if request.client else None,
        is_trusted=False,
    )
    session.add(new_device)
    await session.commit()

    return True


async def get_user_devices(
    session: AsyncSession,
    user_id: str,
) -> list[dict]:
    from backend.app.db.models import DeviceFingerprint as DeviceFingerprintModel

    result = await session.execute(
        select(DeviceFingerprintModel)
        .where(DeviceFingerprintModel.user_id == user_id)
        .order_by(DeviceFingerprintModel.created_at.desc())
    )
    devices = result.scalars().all()
    return [
        {
            "id": d.id,
            "fingerprint_hash": d.fingerprint_hash[:8] + "...",
            "device_info": d.device_info,
            "ip_address": d.ip_address,
            "is_trusted": d.is_trusted,
            "last_seen_at": d.last_seen_at,
            "created_at": d.created_at,
        }
        for d in devices
    ]


async def trust_device(
    session: AsyncSession,
    device_id: str,
    user_id: str,
) -> None:
    from backend.app.db.models import DeviceFingerprint as DeviceFingerprintModel

    device = await session.get(DeviceFingerprintModel, device_id)
    if not device or device.user_id != user_id:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Device not found")
    device.is_trusted = True
    device.last_seen_at = datetime.now(UTC)
    await session.commit()


async def remove_device(
    session: AsyncSession,
    device_id: str,
    user_id: str,
) -> None:
    from backend.app.db.models import DeviceFingerprint as DeviceFingerprintModel

    device = await session.get(DeviceFingerprintModel, device_id)
    if not device or device.user_id != user_id:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Device not found")
    await session.delete(device)
    await session.commit()
