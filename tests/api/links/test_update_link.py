import asyncio
import datetime
import pytest
import pytest_asyncio

import logging

from api.v1.schemas.links import LinkInDB

pytestmark = pytest.mark.asyncio

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


async def test_update_link(client, auth_headers, created_link):
    """Test updating a link."""
    short_code = created_link["short_code"]
    new_original_url = "https://new-url.com/"

    new_expires_at = (datetime.datetime.now(datetime.timezone.utc) + datetime.timedelta(days=30)).strftime(
        "%Y-%m-%dT%H:%M:%SZ"
    )

    response = await client.put(
        f"/v1/links/{short_code}",
        headers=auth_headers,
        json={"link_data": {"original_url": new_original_url, "expires_at": new_expires_at}},
    )
    assert response.status_code == 204, f"Failed to update link: {response.text}"


async def test_update_non_existent_link(client, auth_headers):
    """Test updating a non-existent link."""
    short_code = "nonexistentcode"
    new_original_url = "https://new-url.com/"

    response = await client.put(
        f"/v1/links/{short_code}",
        headers=auth_headers,
        json={"link_data": {"original_url": new_original_url}},
    )
    assert response.status_code == 404, f"Expected 404 for non-existent link, got: {response.text}"


async def test_update_link_with_invalid_data(client, auth_headers, created_link):
    """Test updating a link with invalid data."""
    short_code = created_link["short_code"]
    new_original_url = "invalid-url"

    response = await client.put(
        f"/v1/links/{short_code}",
        headers=auth_headers,
        json={"link_data": {"original_url": new_original_url}},
    )
    assert response.status_code == 422, f"Expected 422 for invalid URL, got: {response.text}"


async def test_update_link_with_None_expires_at(client, auth_headers, created_link):
    """Test updating a link with None expires_at."""
    short_code = created_link["short_code"]
    new_original_url = "https://new-url.com/"

    response = await client.put(
        f"/v1/links/{short_code}",
        headers=auth_headers,
        json={"link_data": {"original_url": new_original_url, "expires_at": None}},
    )
    assert response.status_code == 204


async def test_update_already_expired(client, auth_headers, created_link):
    """Test updating a link that is already expired."""
    short_code = created_link["short_code"]
    new_original_url = "https://new-url.com/"
    new_expires_at = (datetime.datetime.now(datetime.timezone.utc) - datetime.timedelta(days=1)).strftime(
        "%Y-%m-%dT%H:%M:%SZ"
    )

    response = await client.put(
        f"/v1/links/{short_code}",
        headers=auth_headers,
        json={"link_data": {"original_url": new_original_url, "expires_at": new_expires_at}},
    )
    assert response.status_code == 422, f"Expected 422 for already expired link, got: {response.text}"


async def test_update_invalid_user(client, created_link):
    """Test updating a link with an invalid user."""
    short_code = created_link["short_code"]
    new_original_url = "https://new-url.com/"
    new_expires_at = (datetime.datetime.now(datetime.timezone.utc) + datetime.timedelta(days=30)).strftime(
        "%Y-%m-%dT%H:%M:%SZ"
    )

    response = await client.put(
        f"/v1/links/{short_code}",
        headers={"Authorization": "Bearer invalid_token"},
        json={"link_data": {"original_url": new_original_url, "expires_at": new_expires_at}},
    )
    assert response.status_code == 401, f"Expected 401 for invalid user, got: {response.text}"


async def test_update_other_user(client, other_auth_headers, created_link):
    """Test updating a link that belongs to another user."""
    short_code = created_link["short_code"]
    new_original_url = "https://new-url.com/"
    new_expires_at = (datetime.datetime.now(datetime.timezone.utc) + datetime.timedelta(days=30)).strftime(
        "%Y-%m-%dT%H:%M:%SZ"
    )

    response = await client.put(
        f"/v1/links/{short_code}",
        headers=other_auth_headers,
        json={"link_data": {"original_url": new_original_url, "expires_at": new_expires_at}},
    )
    assert response.status_code == 403, f"Expected 403 for unauthorized access, got: {response.text}"
