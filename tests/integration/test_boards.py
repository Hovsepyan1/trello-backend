import pytest
from httpx import AsyncClient

from tests.conftest import auth_header, create_test_user, login_user


@pytest.mark.anyio
async def test_create_board_succes(client: AsyncClient):
    user = await create_test_user(client)
    tokens = await login_user(client)
    headers = auth_header(tokens["access_token"])

    response = await client.post(
        "/boards",
        json = {
            "name": "First board",
            "description": "first board description"
        },
        headers=headers
    )
    assert response.status_code == 201
    data = response.json()
    assert "id" in data
    assert data["name"] == "First board"
    assert data["description"] == "first board description"
    assert data["owner_id"] == user["id"]
    assert len(data["members"]) == 1
    assert data["members"][0]["first_name"] == user["first_name"]
    assert data["members"][0]["last_name"] == user["last_name"]

@pytest.mark.anyio
async def test_create_board_anauthorized(client):
    response = await client.post(
        "/boards",
        json={
            "name" : "test",
            "description" : "test"
        }
    )

    assert response.status_code == 401
    assert response.json()["detail"] == "Not authenticated"

@pytest.mark.anyio
async def test_get_boards_empty(client):
    user = await create_test_user(client)
    tokens = await login_user(client)
    headers = auth_header(tokens["access_token"])

    response = await client.get("/boards/all", headers=headers)
    
    assert response.status_code == 200
    assert len(response.json()) == 0

@pytest.mark.anyio
async def test_get_boards(client: AsyncClient):
    user = await create_test_user(client)
    tokens = await login_user(client)
    headers = auth_header(tokens["access_token"])

    for i in range(10):
        response_board = await client.post(
            "/boards",
            json={"name" : f"name{i}", "description" : f"description{i}"},
            headers = headers
        )
        assert response_board.status_code == 201

    response = await client.get("/boards/all", headers=headers)
    assert response.status_code == 200
    assert len(response.json()) == 10

@pytest.mark.anyio
@pytest.mark.parametrize("limit, offset, expected_len", [
    (5, 0, 5),
    (2, 0, 2),
    (3, 2, 3),
    (100, 0, 10),
    (5, 8, 2)
])
async def test_get_boards_with_pagination(client: AsyncClient, limit, offset, expected_len):
    user = await create_test_user(client)
    tokens = await login_user(client)
    headers = auth_header(tokens["access_token"])

    for i in range(10):
        response_board = await client.post(
            "/boards",
            json={"name" : f"name{i}", "description" : f"description{i}"},
            headers = headers
        )
        assert response_board.status_code == 201

    response = await client.get("/boards", params={"limit": limit, "offset": offset}, headers=headers)
    assert len(response.json()) == expected_len

@pytest.mark.anyio
async def test_get_board_by_id(client: AsyncClient, test_board):
    tokens = await login_user(client)
    headers = auth_header(tokens["access_token"])

    board_id = test_board["id"]
    response = await client.get(f"/boards/{board_id}", headers=headers)

    assert response.status_code == 200
    data = response.json()
    assert data["id"] == board_id
    assert data["name"] == "test"
    assert data["description"] == "test"

@pytest.mark.anyio
async def test_delete_board(client: AsyncClient, test_board):
    tokens = await login_user(client)
    headers = auth_header(tokens["access_token"])

    board_id = test_board["id"]
    response = await client.delete(f"/boards/{board_id}", headers= headers)
    assert response.status_code == 204

@pytest.mark.anyio
async def test_update_board(client: AsyncClient, test_board):
    tokens = await login_user(client)
    headers = auth_header(tokens["access_token"])

    board_id = test_board["id"]
    response = await client.patch(f"/boards/{board_id}", json={"name" : "name2", "description" : "description2"}, headers=headers)
    assert response.status_code == 200
    data = response.json()
    assert data["name"] == "name2"
    assert data["description"] == "description2"

@pytest.mark.anyio
async def test_update_board_wrong_user(client: AsyncClient, test_board):
    tokens1 = await login_user(client)
    headers1 = auth_header(tokens1["access_token"])

    board_id = test_board["id"]

    await create_test_user(client, first_name="user2", last_name="user2", email="user2@gmail.com")
    tokens2 = await login_user(client, email="user2@gmail.com")
    headers2 = auth_header(tokens2["access_token"])

    response = await client.patch(f"/boards/{board_id}", json={"name" : "name2", "description" : "description2"}, headers=headers2)
    assert response.status_code == 403
    assert response.json()["detail"] == "You do not have access to this board"


@pytest.mark.anyio
async def test_board_invite_join(client: AsyncClient, test_board):
    tokens1 = await login_user(client)
    headers1 = auth_header(tokens1["access_token"])

    board_id = test_board["id"]

    await create_test_user(client, first_name="user2", last_name="user2", email="user2@gmail.com")
    tokens2 = await login_user(client, email="user2@gmail.com")
    headers2 = auth_header(tokens2["access_token"])
    response_inviter = await client.get(f"/boards/{board_id}/invite", headers = headers1)

    assert response_inviter.status_code == 200
    token = response_inviter.json()["token"]
    response_joiner = await client.post(f"/boards/join/{token}", headers = headers2)
    assert response_joiner.status_code == 200
    assert response_joiner.json()["message"] == "Successfully joined to board"