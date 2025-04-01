import asyncio
import datetime
import pytest
import pytest_asyncio

import logging

from api.v1.schemas.links import LinkInDB

pytestmark = pytest.mark.asyncio

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


async def test_get_link(client, created_link):
    """Helper function to get a link by its short code."""
    short_code = created_link["short_code"]

    response = await client.get(f"/v1/links/{short_code}")
    assert response.status_code == 307, f"Failed to get link: {response.text}"
    assert response.headers["Location"] == "https://vk.ru/", "Redirect location mismatch"


async def test_get_link_from_cache(client, created_link):
    """Test retrieving a link from the cache."""
    short_code = created_link["short_code"]

    # Simulate storing the link in the cache

    response = await client.get(f"/v1/links/{short_code}")
    response = await client.get(f"/v1/links/{short_code}")
    assert response.status_code == 307, f"Failed to get link from cache: {response.text}"
    assert response.headers["Location"] == "https://vk.ru/", "Redirect location mismatch"
    

async def test_cache(client, created_link, redis_client):
    """Test that the link is cached in Redis."""
    short_code = created_link["short_code"]

    cache_link = redis_client.get(short_code)
    assert cache_link is None, "Link should not be in cache yet"

    # Simulate storing the link in the cache
    await client.get(f"/v1/links/{short_code}")
    
    # Check if the link is now in the cache
    cache_link = redis_client.get(short_code)
    assert LinkInDB.model_validate_json(cache_link).short_code == short_code, "Link should be in cache"

