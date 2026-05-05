import pytest
from sqlalchemy import delete
from sqlalchemy.ext.asyncio import async_sessionmaker

import auth
from database import engine
from models import Emergency, User


@pytest.fixture
async def db_session():
    session_factory = async_sessionmaker(engine, expire_on_commit=False)
    async with session_factory() as session:
        await session.execute(delete(Emergency))
        await session.execute(delete(User))
        await session.commit()
        yield session


@pytest.mark.integration
@pytest.mark.asyncio
async def test_create_and_list_emergency_real_postgres(client, db_session):
    user = User(username="integration-user", email="int@example.com", hashed_password="x", is_active=True)
    db_session.add(user)
    await db_session.commit()
    await db_session.refresh(user)

    async def fake_current_user():
        return user

    from main import app

    app.dependency_overrides[auth.get_current_user] = fake_current_user

    create_resp = await client.post(
        "/api/v1/emergencies/",
        json={"latitude": -23.55, "longitude": -46.63, "description": "Queda de moto"},
        headers={"Authorization": "Bearer any-token"},
    )
    assert create_resp.status_code == 201

    list_resp = await client.get(
        "/api/v1/emergencies/",
        headers={"Authorization": "Bearer any-token"},
    )
    assert list_resp.status_code == 200
    payload = list_resp.json()
    assert len(payload) >= 1
    assert payload[0]["description"] == "Queda de moto"


@pytest.mark.integration
@pytest.mark.asyncio
async def test_get_nonexistent_emergency_returns_404_real_postgres(client, db_session):
    user = User(username="integration-user-2", email="int2@example.com", hashed_password="x", is_active=True)
    db_session.add(user)
    await db_session.commit()
    await db_session.refresh(user)

    async def fake_current_user():
        return user

    from main import app

    app.dependency_overrides[auth.get_current_user] = fake_current_user
    resp = await client.get("/api/v1/emergencies/99999", headers={"Authorization": "Bearer any-token"})
    assert resp.status_code == 404
