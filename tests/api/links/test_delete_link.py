import asyncio
import datetime
import pytest
import pytest_asyncio

import logging

from api.v1.schemas.links import LinkInDB

pytestmark = pytest.mark.asyncio

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


async def test_delete_link(client, auth_headers, created_link):
    """Test deleting a link."""
    short_code = created_link["short_code"]

    response = await client.delete(
        f"/v1/links/{short_code}",
        headers=auth_headers,
    )
    assert response.status_code == 204, f"Failed to delete link: {response.text}"
    # Check if the link is actually deleted
    response = await client.get(f"/v1/links/{short_code}")
    assert response.status_code == 404, f"Expected 404 for deleted link, got: {response.text}"


async def test_delete_non_existent_link(client, auth_headers):
    """Test deleting a non-existent link."""
    short_code = "nonexistentcode"

    response = await client.delete(
        f"/v1/links/{short_code}",
        headers=auth_headers,
    )
    assert response.status_code == 404, f"Expected 404 for non-existent link, got: {response.text}"


async def test_delete_link_without_auth(client, created_link):
    """Test deleting a link without authentication."""
    short_code = created_link["short_code"]

    response = await client.delete(f"/v1/links/{short_code}")
    assert response.status_code == 401, "Expected 401 for unauthenticated request"


async def test_delete_valid_non_existed_token(client, created_link, valid_non_existed_auth_headers):
    """Test deleting a link with an invalid token."""
    short_code = created_link["short_code"]

    response = await client.delete(
        f"/v1/links/{short_code}",
        headers=valid_non_existed_auth_headers,
    )
    assert response.status_code == 401, "Expected 401 for invalid token"


async def test_delete_other_user_link(client, other_auth_headers, created_link):
    """Test deleting a link that belongs to another user."""
    short_code = created_link["short_code"]

    response = await client.delete(
        f"/v1/links/{short_code}",
        headers=other_auth_headers,
    )
    assert response.status_code == 403, f"Expected 403 for unauthorized access, got: {response.text}"
