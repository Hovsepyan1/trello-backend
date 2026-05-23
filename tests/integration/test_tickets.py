import pytest
from httpx import AsyncClient

from tests.conftest import auth_header, create_test_user, login_user


@pytest.mark.anyio
async def test_get_tickets_empty(client: AsyncClient, test_section):
    tokens = await login_user(client)
    headers = auth_header(tokens["access_token"])

    section_id = test_section["id"]
    response = await client.get(f"/sections/{section_id}", headers=headers)
    assert response.status_code == 200
    data = response.json()
    assert data["name"] == "test"
    assert data["description"] == "test"
    assert len(data["tickets"]) == 0

@pytest.mark.anyio
async def test_create_ticket_succes(client: AsyncClient, test_section):
    tokens = await login_user(client)
    headers = auth_header(tokens["access_token"])

    section_id = test_section["id"]

    user2 = await create_test_user(client, email="testemail@example.com")
    response = await client.post(
        f"/sections/{section_id}/tickets", 
        json={"name":"test1", "description":"test1", "due_to": "2026-06-14T15:16", "user_id" : user2["id"]},
        headers=headers
    )

    assert response.status_code == 201

@pytest.mark.anyio
async def test_get_tickets(client: AsyncClient, test_section):
    tokens = await login_user(client)
    headers = auth_header(tokens["access_token"])

    section_id = test_section["id"]

    user2 = await create_test_user(client, email="testemail@example.com")
    for i in range(10):
        response = await client.post(
            f"/sections/{section_id}/tickets",
            json={"name" : f"name{i}", "description" : f"description{i}", "due_to" : "2026-06-14T15:16", "user_id" : user2["id"]},
            headers = headers
        )
        assert response.status_code == 201

    response = await client.get(f"/sections/{section_id}/tickets", headers=headers)
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
async def test_get_tickets_with_pagination(client: AsyncClient, limit, offset, expected_len, test_section):
    tokens = await login_user(client)
    headers = auth_header(tokens["access_token"])
    section_id = test_section["id"]
    user2 = await create_test_user(client, email="testemail@example.com")

    for i in range(10):
        response = await client.post(
            f"/sections/{section_id}/tickets",
            json={"name" : f"name{i}", "description" : f"description{i}", "due_to" : "2026-06-14T15:16", "user_id" : user2["id"]},
            headers = headers
        )
        assert response.status_code == 201

    response = await client.get(f"/sections/{section_id}/tickets", params={"limit": limit, "offset": offset}, headers=headers)
    assert len(response.json()) == expected_len

@pytest.mark.anyio
async def test_get_ticket_by_id(client: AsyncClient, test_ticket):
    tokens = await login_user(client)
    headers = auth_header(tokens["access_token"])
    ticket_id = test_ticket["id"]
    response_ticket = await client.get(f"/tickets/{ticket_id}", headers=headers)
    ticket = response_ticket.json()
    assert ticket["id"] == ticket_id
    assert ticket["section_id"] == test_ticket["section_id"]
    assert ticket["name"] == "test"
    assert ticket["description"] == "test"

@pytest.mark.anyio
async def test_get_ticket_by_id_with_wrong_user(client: AsyncClient, test_ticket):
    await create_test_user(client, email="user2@gmail.com")
    tokens2 = await login_user(client, email="user2@gmail.com")
    headers2 = auth_header(tokens2["access_token"])

    ticket_id = test_ticket["id"]

    response_ticket = await client.get(f"/tickets/{ticket_id}", headers=headers2)
    assert response_ticket.status_code == 403
    assert response_ticket.json()["detail"] == "You do not have access to this ticket"

@pytest.mark.anyio
async def test_update_ticket(client: AsyncClient, test_ticket):
    tokens = await login_user(client)
    headers = auth_header(tokens["access_token"])
    ticket_id = test_ticket["id"]

    response_ticket = await client.patch(f"tickets/{ticket_id}", json={"name": "update", "description" : "update"}, headers= headers)
    assert response_ticket.status_code == 200
    ticket = response_ticket.json()

    assert ticket["name"] == "update"
    assert ticket["description"] == "update"
    assert ticket["section_id"] == test_ticket["section_id"]

@pytest.mark.anyio
async def test_update_ticket_wrong_user(client: AsyncClient, test_ticket):
    user2 = await create_test_user(client, email="user2@gmail.com")
    tokens2 = await login_user(client, email="user2@gmail.com")
    headers2 = auth_header(tokens2["access_token"])

    ticket_id = test_ticket["id"]

    response_ticket = await client.patch(f"/tickets/{ticket_id}", json={"name": "update", "description" : "update"}, headers=headers2)
    assert response_ticket.status_code == 403
    assert response_ticket.json()["detail"] == "You do not have access to this ticket" 

@pytest.mark.anyio
async def test_delete_ticket(client: AsyncClient, test_ticket):
    tokens = await login_user(client)
    headers = auth_header(tokens["access_token"])

    ticket_id = test_ticket["id"]

    response_ticket = await client.delete(f"tickets/{ticket_id}", headers= headers)
    assert response_ticket.status_code == 204

@pytest.mark.anyio 
async def test_delete_ticket_wrong_user(client: AsyncClient, test_ticket):
    await create_test_user(client, email="user2@gmail.com")
    tokens2 = await login_user(client, email="user2@gmail.com")
    headers2 = auth_header(tokens2["access_token"])

    ticket_id = test_ticket["id"]

    response_ticket = await client.delete(f"/tickets/{ticket_id}", headers=headers2)
    assert response_ticket.status_code == 403
    assert response_ticket.json()["detail"] == "You do not have access to this ticket"