import pytest
from httpx import AsyncClient


pytestmark = pytest.mark.asyncio

async def test_health_check(client: AsyncClient) -> None:
    response = await client.get("/")
    assert response.status_code == 200
    assert response.json() == {"status": "App healthy"}
