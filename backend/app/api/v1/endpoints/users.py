from fastapi import APIRouter, Depends
from sqlalchemy.ext.asyncio import AsyncSession

from backend.app.api.deps import get_current_user
from backend.app.core.database import get_db_session
from backend.app.db.user import User
from backend.app.schemas.users import ProfileResponse, UpdateProfileRequest
from backend.app.services.user_service import UserService

router = APIRouter(prefix="/users", tags=["users"])
user_service = UserService()


@router.get("/me", response_model=ProfileResponse)
async def get_profile(
    current_user: User = Depends(get_current_user),
    session: AsyncSession = Depends(get_db_session),
) -> ProfileResponse:
    return await user_service.get_profile(session, current_user)


@router.patch("/me", response_model=ProfileResponse)
async def update_profile(
    payload: UpdateProfileRequest,
    current_user: User = Depends(get_current_user),
    session: AsyncSession = Depends(get_db_session),
) -> ProfileResponse:
    return await user_service.update_profile(session, current_user, payload)
