import asyncio
import datetime
from unittest.mock import patch
import pytest
import pytest_asyncio

import logging

pytestmark = pytest.mark.asyncio

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


async def test_create_link_success(client, auth_headers, base_link):
    """Test creating a link successfully."""
    response = await client.post("/v1/links/shorten", json=base_link, headers=auth_headers)

    assert response.status_code == 200, "Link creation failed"
    assert "short_code" in response.json(), "Shortened URL not found in response"


async def test_non_authenticated_create_link(client, base_link):
    """Test creating a link without authentication."""
    response = await client.post("/v1/links/shorten", json=base_link)

    assert response.status_code == 200, "Link creation failed"
    assert "short_code" in response.json(), "Shortened URL not found in response"


async def test_valid_non_existed_auth_headers(client, base_link, valid_non_existed_auth_headers):
    logger.info("Testing with valid non-existent auth headers")
    response = await client.post("/v1/links/shorten", headers=valid_non_existed_auth_headers, json=base_link)
    assert response.status_code == 200, f"Request should fail with non-existent auth headers {response.json()}"


async def test_create_custom_alias_link(client, auth_headers, custom_alias_link):
    """Test creating a link with a custom alias."""
    response = await client.post("/v1/links/shorten", json=custom_alias_link, headers=auth_headers)

    assert response.status_code == 200, "Link creation with custom alias failed"
    assert "short_code" in response.json(), "Shortened URL not found in response"
    assert response.json()["short_code"] == custom_alias_link["custom_alias"], "Custom alias mismatch"


async def test_create_expired_link(client, auth_headers, expired_link):
    """Test creating a link with an expiration date."""
    response = await client.post("/v1/links/shorten", json=expired_link, headers=auth_headers)
    print(response.text)  # Debugging output
    assert response.status_code == 200, f"Link creation with expiration date failed {response.text}"
    assert "short_code" in response.json(), "Shortened URL not found in response"
    assert response.json()["expires_at"] == expired_link["expires_at"], "Expiration date mismatch"


async def test_expired_at_past_link(client, auth_headers, expired_link):
    """Test creating a link with an expiration date in the past."""
    expired_link["expires_at"] = (datetime.datetime.now(datetime.timezone.utc) - datetime.timedelta(days=1)).strftime(
        "%Y-%m-%dT%H:%M:%SZ"
    )
    response = await client.post("/v1/links/shorten", json=expired_link, headers=auth_headers)

    assert response.status_code == 422, "Link creation with past expiration date should fail"
    assert "detail" in response.json(), "Error detail not found in response"
    
    
async def test_create_link_with_same_custom_alias(client, auth_headers, custom_alias_link):
    """Test creating a link with the same custom alias."""
    # Create the first link with the custom alias
    response = await client.post("/v1/links/shorten", json=custom_alias_link, headers=auth_headers)
    assert response.status_code == 200, "Link creation with custom alias failed"

    # Attempt to create a second link with the same custom alias
    response = await client.post("/v1/links/shorten", json=custom_alias_link, headers=auth_headers)

    assert response.status_code == 400, "Link creation with duplicate custom alias should fail"


@pytest.mark.parametrize(
    "invalid_custom_alias",
    [
        "invalid alias",  # Spaces not allowed
        "testalias!",  # Special characters not allowed
        "testalias12345678901234567890123456789012345678901234567890",  # Too long
        "search",
        "expired",
    ],
)
async def test_create_link_with_invalid_custom_alias(client, auth_headers, invalid_custom_alias, base_link):
    """Test creating a link with an invalid custom alias."""
    base_link["custom_alias"] = invalid_custom_alias
    response = await client.post("/v1/links/shorten", json=base_link, headers=auth_headers)

    assert response.status_code == 400, "Link creation with invalid custom alias should fail"
    assert "detail" in response.json(), "Error detail not found in response"


async def test_retries_create_short_code(client, base_link):
    # mock links_service._generate_short_code
    # to simulate a failure
    
    with patch("api.v1.services.links.LinksService._generate_short_code", return_value="testalias") as mock_generate_short_code:
        response = await client.post("/v1/links/shorten", json=base_link)
        response = await client.post("/v1/links/shorten", json=base_link)
        assert response.status_code == 400, "Link creation should fail after retries"