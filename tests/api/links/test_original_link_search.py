import asyncio
import datetime
import pytest
import pytest_asyncio

import logging

from api.v1.schemas.links import LinkInDB

pytestmark = pytest.mark.asyncio

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


async def test_original_link_search(client, created_link):
    """Test searching for an original link."""
    original_url = "https://vk.ru/"
    short_code = created_link["short_code"]

    response = await client.get(f"/v1/links/search", params={"original_link": original_url})
    assert response.status_code == 200, f"Failed to get original link: {response.text}"
    assert len(response.json()["links"]) == 1, "Expected one link in response"
    assert response.json()["links"][0]["original_url"] == original_url, "Original URL mismatch"


async def test_search_no_short_links(client):
    """Test searching for a non-existent original link."""
    original_url = "https://nonexistentlink.com/"

    response = await client.get(f"/v1/links/search", params={"original_link": original_url})
    assert response.status_code == 200, f"Failed to search for non-existent link: {response.text}"
    assert len(response.json()["links"]) == 0, "Expected no links in response"


