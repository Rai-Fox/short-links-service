from typing import Generator, AsyncGenerator

from sqlalchemy import create_engine, Engine
from sqlalchemy.orm import sessionmaker, Session
from sqlalchemy.ext.asyncio import create_async_engine, AsyncEngine
from sqlalchemy.ext.asyncio import async_sessionmaker, AsyncSession

from core.config import get_settings
from core.logging import get_logger
from db.models.base import Base

logger = get_logger(__name__)


def get_engine() -> Engine:
    engine = create_engine(
        get_settings().db_settings.CONNECTION_URL,
        echo=get_settings().db_settings.ECHO,
        pool_size=get_settings().db_settings.POOL_SIZE,
        max_overflow=get_settings().db_settings.MAX_OVERFLOW,
    )
    return engine


def get_async_engine() -> AsyncEngine:
    engine = create_async_engine(
        get_settings().db_settings.ASYNC_CONNECTION_URL,
        echo=get_settings().db_settings.ECHO,
        pool_size=get_settings().db_settings.POOL_SIZE,
        max_overflow=get_settings().db_settings.MAX_OVERFLOW,
    )
    return engine


sync_session_factory = sessionmaker(autocommit=False, autoflush=False, bind=get_engine())
async_session_factory = async_sessionmaker(
    autocommit=False, autoflush=False, bind=get_async_engine(), expire_on_commit=False
)


def get_db_session() -> Generator[Session, None, None]:
    """
    FastAPI dependency: Provides a sync SQLAlchemy session managed with try/finally.
    """
    with sync_session_factory() as session:
        try:
            yield session
            session.commit()
        except Exception:
            logger.exception("Sync session rollback due to exception")
            raise


async def get_async_db_session() -> AsyncGenerator[AsyncSession, None]:
    """
    FastAPI dependency: Provides an async SQLAlchemy session managed with async with.
    Handles commit, rollback, and closing automatically.
    """
    async with async_session_factory() as session:
        try:
            yield session
            await session.commit()
        except Exception:
            logger.exception("Async session rollback due to exception")
            raise


async def create_tables() -> None:
    async_engine = get_async_engine()
    async with async_engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)
    await async_engine.dispose()


async def drop_tables() -> None:
    async_engine = get_async_engine()
    async with async_engine.begin() as conn:
        await conn.run_sync(Base.metadata.drop_all)
    await async_engine.dispose()
