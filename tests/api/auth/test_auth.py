import pytest
import pytest_asyncio
import logging

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


pytestmark = pytest.mark.asyncio


async def test_register_user_success(client):
    payload = {"username": "newuser", "password": "newpassword"}
    logger.info("Testing user registration with payload: %s", payload)
    response = await client.post("/v1/auth/register", json=payload)
    assert response.status_code == 200
    assert "access_token" in response.json()


async def test_login_user_success(client, credentials):
    logger.info("Testing user login with credentials: %s", credentials)
    response = await client.post("/v1/auth/register", json=credentials)
    assert response.status_code == 200
    response = await client.post("/v1/auth/login", json=credentials)
    assert response.status_code == 200
    assert "access_token" in response.json()


async def test_register_existing_user(client, credentials):
    logger.info("Testing registration of an existing user with credentials: %s", credentials)
    response = await client.post("/v1/auth/register", json=credentials)
    response = await client.post("/v1/auth/register", json=credentials)
    assert response.status_code == 400


async def test_login_nonexistent_user(client):
    payload = {"username": "nonexistentuser", "password": "wrongpassword"}
    logger.info("Testing login with nonexistent user: %s", payload)
    response = await client.post("/v1/auth/login", json=payload)
    assert response.status_code == 404, "Login should fail for nonexistent user"


async def test_login_wrong_password(client, credentials):
    logger.info("Testing login with wrong password for user: %s", credentials["username"])
    # First register the user
    response = await client.post("/v1/auth/register", json=credentials)
    assert response.status_code == 200, "User registration failed"
    # Now attempt to login with the wrong password
    payload = {"username": credentials["username"], "password": "wrongpassword"}
    response = await client.post("/v1/auth/login", json=payload)
    assert response.status_code == 401, "Login should fail for wrong password"
