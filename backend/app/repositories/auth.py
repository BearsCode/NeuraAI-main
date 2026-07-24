from __future__ import annotations

from sqlalchemy import select

from backend.app.db.refresh_token_session import RefreshTokenSession
from backend.app.repositories.base import BaseRepository


class RefreshSessionRepository(BaseRepository[RefreshTokenSession]):
    async def get_by_token_hash(self, token_hash: str) -> RefreshTokenSession | None:
        return await self.session.scalar(
            select(RefreshTokenSession).where(
                RefreshTokenSession.token_id_hash == token_hash
            )
        )

    async def create(self, refresh_session: RefreshTokenSession) -> RefreshTokenSession:
        self.session.add(refresh_session)
        await self.session.flush()
        return refresh_session
