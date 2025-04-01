import pytest
import pytest_asyncio
from unittest.mock import MagicMock
import datetime
import logging
import jwt
import os

pytestmark = pytest.mark.asyncio

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


DATETIME = datetime.datetime.fromisoformat("2025-01-01T00:00:00Z")


@pytest.fixture
def mocking_datetime_now(monkeypatch):
    datetime_mock = MagicMock(wrap=datetime.datetime)
    datetime_mock.now.return_value = DATETIME

    monkeypatch.setattr(datetime, "datetime", datetime_mock)


@pytest.fixture(scope="function")
def base_link():
    return {
        "original_url": "https://vk.ru/",
    }


@pytest.fixture(scope="function")
def base_link_2():
    return {
        "original_url": "https://example.com/",
    }


@pytest.fixture(scope="function")
def custom_alias_link():
    return {
        "original_url": "https://vk.ru/",
        "custom_alias": "testalias",
    }


@pytest.fixture(scope="function")
def custom_alias_link_2():
    return {
        "original_url": "https://vk.ru/",
        "custom_alias": "testalias2",
    }


@pytest.fixture(scope="function")
def expired_link():
    return {
        "original_url": "https://vk.ru/",
        "expires_at": (datetime.datetime.now(datetime.timezone.utc) + datetime.timedelta(seconds=10)).strftime(
            "%Y-%m-%dT%H:%M:%SZ"
        ),
    }


@pytest.fixture(scope="session")
def valid_non_existed_auth_headers():
    auth_token = jwt.encode(
        {
            "sub": "non_existed_user",
            "exp": datetime.datetime.now(datetime.timezone.utc) + datetime.timedelta(minutes=30),
        },
        key=os.getenv("JWT_SECRET_KEY"),
        algorithm=os.getenv("JWT_ALGORITHM"),
    )
    return {
        "Authorization": f"Bearer {auth_token}",
    }


@pytest_asyncio.fixture(scope="function")
async def created_link(client, auth_headers, base_link):
    """Creates a link and returns its short code."""
    response = await client.post("/v1/links/shorten", json=base_link, headers=auth_headers)
    assert response.status_code == 200, "Link creation failed"
    return response.json()
