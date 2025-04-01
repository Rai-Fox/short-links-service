import asyncio
import datetime
from httpx import AsyncClient
import pytest
import pytest_asyncio
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import update
import logging


from api.v1.schemas.links import LinkInDB
from db.repositories.links import LinksRepository
from db.models.links import Link

pytestmark = pytest.mark.asyncio

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


async def test_check_expired_links(client: AsyncClient, links_repository: LinksRepository, credentials):
    """Test that expired links are removed from the database."""
    # Create a link with an expiration date in the past
    expired_link = {
        "original_url": "https://expired-link.com",
        "short_code": "exp",
        "created_at": datetime.datetime.now(datetime.timezone.utc) - datetime.timedelta(days=1),
        "expires_at": datetime.datetime.now(datetime.timezone.utc) - datetime.timedelta(days=1),
    }
    await links_repository.create_link(
        short_code=expired_link["short_code"],
        original_url=expired_link["original_url"],
        expires_at=expired_link["expires_at"],
        created_by=credentials["username"],
    )

    # Run the cleanup task
    await links_repository.check_expired_links()

    # Check if the link has been removed from the database
    retrieved_link = await links_repository.get_link_by_short_code("exp")
    assert retrieved_link is None, "Expired link should have been removed"


async def test_get_expired_links(client: AsyncClient, links_repository: LinksRepository, credentials):
    """Test that expired links are removed from the database."""
    # Create a link with an expiration date in the past
    expired_link = {
        "original_url": "https://expired-link.com",
        "short_code": "exp",
        "created_at": datetime.datetime.now(datetime.timezone.utc) - datetime.timedelta(days=1),
        "expires_at": datetime.datetime.now(datetime.timezone.utc) - datetime.timedelta(days=1),
    }
    await links_repository.create_link(
        short_code=expired_link["short_code"],
        original_url=expired_link["original_url"],
        expires_at=expired_link["expires_at"],
        created_by=credentials["username"],
    )

    # Run the cleanup task
    await links_repository.check_expired_links()

    response = await client.get("v1/links/expired")
    assert "expired_links" in response.json()
    assert response.json()["expired_links"][0]["short_code"] == expired_link["short_code"]


async def test_check_unused_links(
    client: AsyncClient, links_repository: LinksRepository, credentials, db_session: AsyncSession
):
    """Test that expired links are removed from the database."""
    # Create a link with an expiration date in the past
    expired_link = {
        "original_url": "https://expired-link.com",
        "short_code": "exp",
        "last_used_at": datetime.datetime.now(datetime.timezone.utc) - datetime.timedelta(days=5),
    }
    await links_repository.create_link(
        short_code=expired_link["short_code"],
        original_url=expired_link["original_url"],
        created_by=credentials["username"],
    )
    # Change last_used_at
    stmt = (
        update(Link)
        .where(Link.short_code == expired_link["short_code"])
        .values(last_used_at=expired_link["last_used_at"])
    )

    await db_session.execute(stmt)

    # Run the cleanup task
    await links_repository.check_unused_links()

    # Check if the link has been removed from the database
    retrieved_link = await links_repository.get_link_by_short_code("exp")
    assert retrieved_link is None, "Expired link should have been removed"
