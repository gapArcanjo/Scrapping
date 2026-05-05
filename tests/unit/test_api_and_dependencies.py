from unittest.mock import AsyncMock

import pytest
from fastapi import HTTPException

import auth
from models import User


@pytest.mark.asyncio
async def test_health_endpoint(client):
    r = await client.get("/health")
    assert r.status_code == 200
    assert r.json() == {"status": "ok"}


@pytest.mark.asyncio
async def test_chat_endpoint_marked_experimental(client):
    async def fake_current_user():
        return User(id=1, username="u", email="u@example.com", hashed_password="x", is_active=True)

    from main import app

    app.dependency_overrides[auth.get_current_user] = fake_current_user
    r = await client.post(
        "/api/v1/chat/message",
        json={"message": "Tenho dor de garganta"},
        headers={"Authorization": "Bearer any-token"},
    )
    assert r.status_code == 200
    assert "experimental" in r.json()["reply"].lower()


@pytest.mark.asyncio
async def test_invalid_token_raises_401():
    fake_db = AsyncMock()
    fake_db.execute = AsyncMock()
    creds = type("Creds", (), {"credentials": "invalid.jwt.token"})()

    with pytest.raises(HTTPException) as exc:
        await auth.get_current_user(credentials=creds, db=fake_db)

    assert exc.value.status_code == 401
