import pytest
from app.helpers import get_pagination, get_board_with_access, get_board_with_owner_access, get_section_with_access, get_ticket_with_access
from app.auth import get_current_user
from tests.conftest import login_user, create_test_user, auth_header
from fastapi import HTTPException
from httpx import AsyncClient

@pytest.mark.parametrize("offset, limit, expected", [
    (0, 10, {"offset": 0, "limit": 10}),   
    (0, 100, {"offset": 0, "limit": 50}),  
    (0, -5, {"offset": 0, "limit": 10}),   
    (10, 5, {"offset": 10, "limit": 5}),   
])
def test_get_pagination_logic(offset, limit, expected):
    assert get_pagination(offset, limit) == expected

@pytest.mark.parametrize("bad_offset", [-1, -100, -999])
def test_get_pagination_error(bad_offset):
    with pytest.raises(HTTPException) as excinfo:
        get_pagination(offset=bad_offset, limit=10)
    
    assert excinfo.value.status_code == 400
    assert "Offset cannot be negative" in excinfo.value.detail


@pytest.mark.anyio
async def test_get_board_with_owner_access_success(client: AsyncClient, test_board, db_session):
    tokens = await login_user(client)
    current_user = await get_current_user(tokens["access_token"], db_session)
    board = await get_board_with_owner_access(test_board["id"], current_user, db_session)

    assert board is not None
    assert board.owner_id == current_user.id

@pytest.mark.anyio
async def test_get_board_with_owner_access_denied(client: AsyncClient, test_board, db_session):
    tokens1 = await login_user(client)
    headers1 = auth_header(tokens1["access_token"])

    await create_test_user(client, email="user2@example.com")
    tokens2 = await login_user(client, email="user2@example.com")
    headers2 = auth_header(tokens2["access_token"])
    current_user = await get_current_user(tokens2["access_token"], db_session)

    invite = await client.get(f"/boards/{test_board["id"]}/invite", headers=headers1)
    await client.post(f"/boards/join/{invite.json()["token"]}", headers=headers2)

    with pytest.raises(HTTPException) as excinfo:
        await get_board_with_owner_access(test_board["id"], current_user, db_session)

    assert excinfo.value.status_code == 403
    assert excinfo.value.detail == "You do not have access to this board"


@pytest.mark.anyio
async def test_get_board_with_access_success(client: AsyncClient, test_board, db_session):
    tokens1 = await login_user(client)
    headers1 = auth_header(tokens1["access_token"])

    await create_test_user(client, email="user2@example.com")
    tokens2 = await login_user(client, email="user2@example.com")
    headers2 = auth_header(tokens2["access_token"])
    current_user = await get_current_user(tokens2["access_token"], db_session)

    invite = await client.get(f"/boards/{test_board["id"]}/invite", headers=headers1)
    await client.post(f"/boards/join/{invite.json()["token"]}", headers=headers2)

    board = await get_board_with_access(test_board["id"], current_user, db_session)
    assert board is not None

@pytest.mark.anyio
async def test_get_board_with_access_denied(client: AsyncClient, test_board, db_session):
    tokens1 = await login_user(client)
    headers1 = auth_header(tokens1["access_token"])
    section = await client.post(f"/boards/{test_board["id"]}/sections", json={"name" : "test", "description" : "test"}, headers=headers1)

    await create_test_user(client, email="user2@example.com")
    tokens2 = await login_user(client, email="user2@example.com")
    current_user = await get_current_user(tokens2["access_token"], db_session)

    with pytest.raises(HTTPException) as excinfo:
        section = await get_section_with_access(section.json()["id"], current_user, db_session)

    assert excinfo.value.status_code == 403
    assert excinfo.value.detail == "You do not have access to this section"


@pytest.mark.anyio
async def test_get_section_with_access_success(client: AsyncClient, test_section, db_session):
    tokens = await login_user(client)

    current_user = await get_current_user(tokens["access_token"], db_session)

    section = await get_section_with_access(test_section["id"], current_user, db_session)

    assert section is not None
    assert section.id == test_section["id"]

@pytest.mark.anyio
async def test_get_ticket_with_access_success(client: AsyncClient, test_ticket, db_session):
    tokens = await login_user(client)

    current_user = await get_current_user(tokens["access_token"], db_session)

    ticket = await get_ticket_with_access(test_ticket["id"], current_user, db_session)

    assert ticket is not None
    assert ticket.id == test_ticket["id"]


@pytest.mark.anyio
async def test_get_ticket_with_access_denied(client: AsyncClient, test_section, test_ticket, db_session):
    tokens1 = await login_user(client)
    headers1 = auth_header(tokens1["access_token"])

    # ticket = await client.get(f"/sections/{test_section["id"]}/tickets", )    
    await create_test_user(client, email="user2@example.com")
    tokens2 = await login_user(client, email="user2@example.com")
    current_user = await get_current_user(tokens2["access_token"], db_session)
    
    with pytest.raises(HTTPException) as excinfo:
        ticket = await get_ticket_with_access(test_ticket["id"], current_user, db_session)

    assert excinfo.value.status_code == 403
    assert excinfo.value.detail == "You do not have access to this ticket"
