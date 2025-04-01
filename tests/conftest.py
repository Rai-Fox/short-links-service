import asyncio
import logging
from typing import AsyncGenerator, Generator, Any
from fastapi import FastAPI
import pytest
import pytest_asyncio
import fakeredis
from unittest.mock import patch
from httpx import AsyncClient, ASGITransport
from sqlalchemy import create_engine
from sqlalchemy.pool import StaticPool, NullPool
from sqlalchemy.ext.asyncio import create_async_engine, async_sessionmaker, AsyncSession, AsyncEngine
from sqlalchemy import delete


def init_env():
    from pathlib import Path
    import sys
    from dotenv import load_dotenv

    sys.path.append(str(Path(__file__).parent.parent))
    sys.path.append(str(Path(__file__).parent.parent / "app"))

    env_path = Path(__file__).parent / ".test_env"
    if env_path.exists():
        load_dotenv(env_path)
    else:
        raise FileNotFoundError(f".env file not found at {env_path}")


init_env()


from main import app as fastapi_app
from db import get_async_db_session, Base
from core.redis import get_redis_client


TEST_DATABASE_URL = "sqlite+aiosqlite:///:memory:"


@pytest.fixture(scope="session")
def event_loop(request: Any) -> Generator[asyncio.AbstractEventLoop, Any, Any]:
    """Create an instance of the default event loop for the session scope."""
    loop = asyncio.get_event_loop_policy().new_event_loop()
    yield loop
    loop.close()


@pytest_asyncio.fixture(scope="session")
async def test_engine() -> AsyncGenerator[AsyncEngine, None]:
    """
    Creates an async SQLAlchemy engine for the test database (SQLite in-memory).
    Uses NullPool suitable for SQLite.
    """
    engine = create_async_engine(TEST_DATABASE_URL, echo=False, poolclass=StaticPool)
    yield engine
    await engine.dispose()


@pytest_asyncio.fixture(scope="session")
async def test_async_session_factory(test_engine: AsyncEngine) -> async_sessionmaker[AsyncSession]:
    """Creates an async session factory bound to the test engine."""
    return async_sessionmaker(
        bind=test_engine,
        class_=AsyncSession,
        expire_on_commit=False,
        autoflush=False,
        autocommit=False,
    )


@pytest_asyncio.fixture(scope="function", autouse=True)
async def manage_tables(test_engine: AsyncEngine) -> AsyncGenerator[None, None]:
    """Creates and drops tables for each test function for isolation."""
    async with test_engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)
    yield
    async with test_engine.begin() as conn:
        await conn.run_sync(Base.metadata.drop_all)


@pytest_asyncio.fixture(scope="function")
async def db_session(
    test_engine: AsyncEngine, test_async_session_factory: async_sessionmaker[AsyncSession]
) -> AsyncGenerator[AsyncSession, None]:
    """
    Provides a clean database state and an async session for each test function.
    Creates tables before the test and drops them afterwards.
    """

    async with test_async_session_factory() as session:
        try:
            yield session
        except Exception:
            await session.rollback()
            raise
        finally:
            pass


@pytest.fixture(scope="session")
def redis_client() -> Generator[fakeredis.FakeRedis, None, None]:
    """
    Provides a mocked async Redis client (FakeRedis) for each test function.
    """
    with fakeredis.FakeRedis(decode_responses=True) as fake_redis:
        fake_redis.flushall()

        yield fake_redis

        fake_redis.flushall()


@pytest.fixture(scope="session")
def app(test_async_session_factory: async_sessionmaker[AsyncSession], redis_client: fakeredis.FakeRedis) -> FastAPI:
    """
    Provides the FastAPI application instance configured for testing.
    Overrides database and Redis dependencies.
    """

    async def override_get_async_db_session() -> AsyncGenerator[AsyncSession, None]:
        """Dependency override yielding a test DB session."""
        async with test_async_session_factory() as session:
            try:
                yield session
                await session.commit()
            except Exception:
                await session.rollback()
                raise
            finally:
                await session.close()

    async def override_get_redis_client() -> fakeredis.aioredis.FakeRedis:
        """Dependency override yielding a fake Redis client."""
        return redis_client

    fastapi_app.dependency_overrides[get_async_db_session] = override_get_async_db_session
    fastapi_app.dependency_overrides[get_redis_client] = override_get_redis_client

    yield fastapi_app

    fastapi_app.dependency_overrides = {}


@pytest_asyncio.fixture(scope="function")
async def client(app: FastAPI) -> AsyncGenerator[AsyncClient, None]:
    """
    Provides an asynchronous HTTP client (httpx) for making requests to the test app.
    """
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as test_client:
        yield test_client


# --- Test User Fixtures ---


@pytest.fixture(scope="function")
def credentials():
    return {
        "username": "testuser",
        "password": "testpassword",
    }


@pytest_asyncio.fixture(scope="function")
async def auth_token(client: AsyncClient, credentials) -> str:
    """Creates a test user and returns an authentication token."""
    response = await client.post("/v1/auth/register", json=credentials)
    assert response.status_code == 200, "User registration failed"
    return response.json().get("access_token")


@pytest_asyncio.fixture(scope="function")
async def auth_headers(auth_token: str) -> dict[str, str]:
    """Returns headers for authenticated requests."""
    return {"Authorization": f"Bearer {auth_token}"}


@pytest_asyncio.fixture(scope="function")
async def other_auth_token(client: AsyncClient) -> str:
    """Creates a other test user and returns an authentication token."""
    response = await client.post("/v1/auth/register", json={"username": "other", "password": "user"})
    assert response.status_code == 200, "User registration failed"
    return response.json().get("access_token")


@pytest_asyncio.fixture(scope="function")
async def other_auth_headers(other_auth_token) -> dict[str, str]:
    """Returns headers for authenticated requests."""
    return {"Authorization": f"Bearer {other_auth_token}"}


# --- Repository Fixtures ---


@pytest.fixture(scope="function")
def users_repository(db_session: AsyncSession):
    """Provides an instance of UsersRepository with the test session."""
    from db.repositories.users import UsersRepository

    return UsersRepository(session=db_session)


@pytest.fixture(scope="function")
def links_repository(db_session: AsyncSession, redis_client: fakeredis.FakeRedis):
    """Provides an instance of LinksRepository with the test session and fake redis."""
    from db.repositories.links import LinksRepository

    repo = LinksRepository(session=db_session, redis_client=redis_client)
    repo.redis_client = redis_client
    return repo
