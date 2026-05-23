import os

import pytest
from httpx import ASGITransport, AsyncClient
from sqlalchemy.ext.asyncio import (AsyncSession, async_sessionmaker,
                                    create_async_engine)
from sqlalchemy.pool import NullPool

os.environ["DATABASE_URL"] = "postgresql+psycopg://postgres:acthovsepyan@localhost:5432/test_db"
os.environ["SECRET_KEY"] = "secretstr" * 7 #it gives error for short secret key

from app.config import settings
from app.database import get_db
from app.models.base import BaseModel
from main import app


@pytest.fixture(scope="session")
def anyio_backend():
    return "asyncio"

@pytest.fixture(scope="session")
def test_engine():
    engine = create_async_engine(
        os.environ["DATABASE_URL"],
        poolclass=NullPool
    )
    return engine

@pytest.fixture(scope="session")
async def setup_database(test_engine):
    async with test_engine.begin() as conn:
        await conn.run_sync(BaseModel.metadata.create_all)

    yield

    async with test_engine.begin() as conn:
        await conn.run_sync(BaseModel.metadata.drop_all)

    await test_engine.dispose()

@pytest.fixture
async def db_session(
    test_engine, 
    setup_database
): 
    conn = await test_engine.connect()
    trans = await conn.begin()

    test_async_session = async_sessionmaker(
        bind=conn,
        class_=AsyncSession,
        expire_on_commit=False,
        join_transaction_mode="create_savepoint"
    )

    async with test_async_session() as session:
        try:
            yield session
        finally:
            await session.close()
            await trans.rollback()
            await conn.close()


@pytest.fixture
async def client(
    db_session: AsyncSession
):
    async def override_get_db():
        yield db_session

    app.dependency_overrides[get_db] = override_get_db

    async with AsyncClient(
        transport=ASGITransport(app=app),
        base_url="http://test"
    ) as ac:
        yield ac

    app.dependency_overrides.clear()

async def create_test_user(
    client: AsyncClient,
    first_name: str = "testuser",
    last_name: str = "testuser",
    email: str = "test@example.com",
    password: str = "testpassword1234"
) -> dict:
    response = await client.post(
        "/auth/register",
        json = {
            "first_name": first_name,
            "last_name": last_name,
            "email": email,
            "password" : password
        }
    )

    assert response.status_code == 201, f"Failed to create user: {response.text}"
    return response.json()

async def login_user(
    client: AsyncClient,
    email: str = "test@example.com",
    password: str = "testpassword1234"
):
    response = await client.post(
        "/auth/login",
        data={
            "username": email,
            "password": password
        }
    )

    assert response.status_code == 200, f"Failed to login: {response.text}"

    return response.json()

def auth_header(token: str) -> dict[str, str]:
    return {"Authorization": f"Bearer {token}"}

@pytest.fixture(scope="function")
async def test_board(client: AsyncClient):
    user = await create_test_user(client)
    tokens = await login_user(client)
    headers = auth_header(tokens["access_token"])

    response = await client.post("/boards", json={"name" : "test", "description" : "test"}, headers=headers)
    assert response.status_code == 201
    data = response.json()
    assert data["owner_id"] == user["id"]
    assert data["name"] == "test"
    assert data["description"] == "test"
    assert len(data["members"]) == 1
    assert len(data["sections"]) == 0
    assert data["members"][0]["first_name"] == user["first_name"]
    assert data["members"][0]["last_name"] == user["last_name"]

    return data

@pytest.fixture(scope="function")
async def test_section(test_board, client: AsyncClient):
    tokens = await login_user(client)
    headers = auth_header(tokens["access_token"])

    board_id = test_board["id"]
    response = await client.post(f"/boards/{board_id}/sections", json={"name" : "test", "description" : "test"}, headers=headers)

    assert response.status_code == 201
    data = response.json()
    assert data["board_id"] == board_id
    assert len(data["tickets"]) == 0
    assert data["name"] == "test"
    assert data["description"] == "test"

    return data

@pytest.fixture
async def test_ticket(test_section, client: AsyncClient):
    tokens = await login_user(client)
    headers = auth_header(tokens["access_token"])

    test_user = await create_test_user(client, email="test-ticket@example.com")
    # token = await login_user(client, email="test-ticket@example.com")
    section_id = test_section["id"]
    response = await client.post(
        f"/sections/{section_id}/tickets",
        json={"name":"test", "description": "test", "due_to": "2026-12-12T23:59:59", "user_id": test_user["id"]}, 
        headers=headers
    )

    assert response.status_code == 201
    data = response.json()
    assert data["name"] == "test"
    assert data["description"] == "test"
    return data