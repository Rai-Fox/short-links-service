import asyncio
import datetime
import pytest
import pytest_asyncio

import logging

from api.v1.schemas.links import LinkInDB

pytestmark = pytest.mark.asyncio

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


async def test_get_expired_linkы(client):
    """Test retrieving an expired link."""
    response = await client.get("/v1/links/expired")
    assert response.status_code == 200, f"Failed to get expired link: {response.text}"
    assert isinstance(response.json(), dict), "Expected a dict"
    assert "expired_links" in response.json(), "Expected 'expired_links' key in response"
