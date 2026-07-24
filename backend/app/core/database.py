from __future__ import annotations

from collections.abc import AsyncIterator

from sqlalchemy import text
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker, create_async_engine

from backend.app.core.configs import settings
from backend.app.db.base import Base


class DatabaseManager:
    def __init__(self) -> None:
        engine_kwargs: dict[str, object] = {
            "echo": settings.db.echo,
            "pool_pre_ping": True,
        }

        if settings.database_uses_sqlite:
            engine_kwargs["connect_args"] = {"check_same_thread": False}
        else:
            engine_kwargs["pool_size"] = settings.db.pool_size
            engine_kwargs["max_overflow"] = settings.db.max_overflow
            engine_kwargs["pool_timeout"] = settings.db.pool_timeout_seconds
            engine_kwargs["pool_recycle"] = settings.db.pool_recycle_seconds

        self.engine = create_async_engine(settings.database_url, **engine_kwargs)
        self.session_factory = async_sessionmaker(
            self.engine,
            class_=AsyncSession,
            expire_on_commit=False,
            autoflush=False,
        )

    async def get_session(self) -> AsyncIterator[AsyncSession]:
        async with self.session_factory() as session:
            if not settings.database_uses_sqlite:
                await session.execute(
                    text("SET statement_timeout = :timeout_ms"),
                    {"timeout_ms": settings.db.statement_timeout_ms},
                )
            yield session

    async def init(self) -> None:
        if settings.db.run_migrations_on_startup:
            async with self.engine.begin() as connection:
                from sqlalchemy import inspect as sa_inspect
                def _table_exists(conn) -> bool:
                    inspector = sa_inspect(conn)
                    return bool(inspector.get_table_names())
                tables_exist = await connection.run_sync(_table_exists)
                if not tables_exist:
                    await connection.run_sync(Base.metadata.create_all)

    async def dispose(self) -> None:
        await self.engine.dispose()

    async def ping(self) -> None:
        async with self.engine.connect() as connection:
            await connection.execute(text("SELECT 1"))


database_manager = DatabaseManager()


async def get_db_session() -> AsyncIterator[AsyncSession]:
    async for session in database_manager.get_session():
        yield session


def get_session_factory() -> async_sessionmaker[AsyncSession]:
    return database_manager.session_factory


async def init_database() -> None:
    await database_manager.init()


async def close_database() -> None:
    await database_manager.dispose()


async def check_database_connection() -> tuple[bool, dict[str, str]]:
    try:
        await database_manager.ping()
    except Exception:
        return False, {
            "driver": settings.database_driver_name,
            "message": "connection failed",
        }
    return True, {
        "driver": settings.database_driver_name,
        "message": "connected",
    }
