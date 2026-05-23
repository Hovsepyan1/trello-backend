import pytest
from httpx import AsyncClient
from sqlalchemy.ext.asyncio import AsyncSession

from app.auth import (create_access_token, get_current_user, hash_password,
                      verify_access_token, verify_password)
from tests.conftest import create_test_user, login_user


def test_hash_password_logic():
    password = "super-secret"
    hashed = hash_password(password)

    assert password != hashed
    assert verify_password(password, hashed) is True
    assert verify_password("wrong-password", hashed) is False


@pytest.mark.anyio
async def test_create_access_token(client: AsyncClient):
    user = await create_test_user(client)
    token = create_access_token({"id" : user["id"], "type" : "access"})

    assert verify_access_token(token, "access") == user["id"]

@pytest.mark.anyio
async def test_get_current_user(client: AsyncClient, db_session: AsyncSession):
    user = await create_test_user(client)
    tokens = await login_user(client)

    current_user = await get_current_user(token = tokens["access_token"], db = db_session)
    assert current_user is not None
    assert current_user.id == user["id"]
    assert current_user.email == "test@example.com"