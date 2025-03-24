from sqlalchemy import create_engine, Engine
from sqlalchemy.orm import sessionmaker
from sqlalchemy.ext.asyncio import create_async_engine, AsyncEngine
from sqlalchemy.ext.asyncio import async_sessionmaker

from core.config import get_settings
from core.logging import get_logger
from db.models.base import Base
from db.models.users import User

logger = get_logger(__name__)


def get_engine() -> Engine:
    engine = create_engine(
        get_settings().db_settings.CONNECTION_URL,
        echo=True,
        pool_size=get_settings().db_settings.POOL_SIZE,
        max_overflow=get_settings().db_settings.MAX_OVERFLOW,
    )
    return engine


def get_async_engine() -> AsyncEngine:
    engine = create_async_engine(
        get_settings().db_settings.ASYNC_CONNECTION_URL,
        echo=True,
        pool_size=get_settings().db_settings.POOL_SIZE,
        max_overflow=get_settings().db_settings.MAX_OVERFLOW,
    )
    return engine


session = sessionmaker(autocommit=False, autoflush=False, bind=get_engine())
async_session = async_sessionmaker(autocommit=False, autoflush=False, bind=get_async_engine())


async def create_tables() -> None:
    async with get_async_engine().connect() as conn:
        async with conn.begin():
            await conn.run_sync(Base.metadata.create_all)
            await conn.commit()


async def drop_tables() -> None:
    async with get_async_engine().connect() as conn:
        async with conn.begin():
            await conn.run_sync(Base.metadata.drop_all)
            await conn.commit()
