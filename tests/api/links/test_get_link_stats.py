import asyncio
import datetime
import pytest
import pytest_asyncio

import logging

from api.v1.schemas.links import LinkInDB

pytestmark = pytest.mark.asyncio

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


async def test_get_link_stats(client, auth_headers, created_link):
    """Test retrieving link statistics."""
    short_code = created_link["short_code"]

    # Simulate some clicks
    for _ in range(5):
        await client.get(f"/v1/links/{short_code}")

    response = await client.get(f"/v1/links/{short_code}/stats", headers=auth_headers)
    assert response.status_code == 200, f"Failed to get link stats: {response.text}"
    assert isinstance(response.json(), dict), "Expected a dict"
    assert "clicks" in response.json(), "Expected 'clicks' key in response"
    assert response.json()["clicks"] == 5, "Click count mismatch"


async def test_get_link_stats_non_existent(client, auth_headers):
    """Test retrieving statistics for a non-existent link."""
    short_code = "nonexistentcode"

    response = await client.get(f"/v1/links/{short_code}/stats", headers=auth_headers)
    assert response.status_code == 404, f"Expected 404 for non-existent link, got: {response.text}"


async def test_get_link_stats_without_auth(client, created_link):
    """Test retrieving link statistics without authentication."""
    short_code = created_link["short_code"]

    response = await client.get(f"/v1/links/{short_code}/stats")
    assert response.status_code == 401, "Expected 401 for unauthenticated request"


async def test_get_link_stats_invalid_token(client, created_link, valid_non_existed_auth_headers):
    """Test retrieving link statistics with an invalid token."""
    short_code = created_link["short_code"]

    response = await client.get(f"/v1/links/{short_code}/stats", headers=valid_non_existed_auth_headers)
    assert response.status_code == 401, "Expected 401 for invalid token"


async def test_get_link_stats_other_user(client, other_auth_headers, created_link):
    """Test retrieving link statistics for another user's link."""
    short_code = created_link["short_code"]

    response = await client.get(f"/v1/links/{short_code}/stats", headers=other_auth_headers)
    assert response.status_code == 403, f"Expected 403 for unauthorized access, got: {response.text}"
    assert "detail" in response.json(), "Expected 'detail' key in response"
