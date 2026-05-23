import pytest
from httpx import AsyncClient

from tests.conftest import auth_header, create_test_user, login_user


@pytest.mark.anyio
async def test_create_user_validation_error(client: AsyncClient):
    response = await client.post("/auth/register", json = {"email" : "testuser"})
    assert response.status_code == 422
    assert "first_name" in response.text

@pytest.mark.anyio
async def test_create_user(client: AsyncClient):
    response = await create_test_user(client)
    assert response["first_name"] == "testuser"
    assert response["last_name"] == "testuser"
    assert "id" in response
    
@pytest.mark.anyio
async def test_update_user(client: AsyncClient):
    await create_test_user(client)
    tokens = await login_user(client)
    headers = auth_header(tokens["access_token"])

    response = await client.patch("/users", json={"first_name" : "update", "last_name": "update", "email": "update@example.com"}, headers=headers)
    assert response.status_code == 200
    data = response.json()
    assert data["first_name"] == "update"
    assert data["last_name"] == "update"

@pytest.mark.anyio
async def test_log_out(client: AsyncClient):
    await create_test_user(client)
    tokens = await login_user(client)
    headers = auth_header(tokens["access_token"])

    response = await client.post("/users/logout", params={"token": tokens["refresh_token"]}, headers=headers)
    assert response.status_code == 204

@pytest.mark.anyio
async def test_log_out_all(client: AsyncClient):
    await create_test_user(client)
    tokens = await login_user(client)
    headers = auth_header(tokens["access_token"])

    response = await client.post("/users/logout-all", headers=headers)
    assert response.status_code == 204


@pytest.mark.anyio
async def test_delete_user(client: AsyncClient):
    await create_test_user(client)
    tokens = await login_user(client)
    headers = auth_header(tokens["access_token"])

    response = await client.delete("/users", headers=headers)
    assert response.status_code == 204