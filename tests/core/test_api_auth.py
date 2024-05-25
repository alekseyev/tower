from datetime import datetime, timedelta, timezone
from unittest.mock import ANY

import pytest_asyncio
from httpx import AsyncClient
from litestar.status_codes import HTTP_200_OK, HTTP_201_CREATED, HTTP_401_UNAUTHORIZED

from backend.api_app import app
from backend.core.crypto import encode_jwt_token
from backend.core.models import User


@pytest_asyncio.fixture
async def http_client():
    async with AsyncClient(app=app, base_url="http://test") as client:
        yield client


async def test_unauthenticated(http_client):
    response = await http_client.get("/me")
    assert response.status_code == HTTP_401_UNAUTHORIZED


async def test_incorrect_login(http_client):
    await User.create_user(email="test@test.me", nickname="test", password="asdf")

    response = await http_client.post("/login", json={"email": "test@test.me", "password": "ASDF"})
    assert response.status_code == HTTP_401_UNAUTHORIZED, response.json()


async def test_login(http_client):
    await User.create_user(email="test@test.me", nickname="test", password="asdf")

    response = await http_client.post("/login", json={"email": "test@test.me", "password": "asdf"})
    assert response.status_code == HTTP_201_CREATED, response.json()

    token = response.json()["token"]
    assert token

    response = await http_client.get("/me", headers={"Authorization": f"Bearer {token}"})
    assert response.status_code == HTTP_200_OK, response.json()
    assert response.json() == {
        "id": ANY,
        "email": "test@test.me",
    }


async def test_register(http_client):
    assert await User.by_email("test@test.me") is None

    response = await http_client.post(
        "/register", json={"email": "test@test.me", "password": "asdf", "nickname": "test"}
    )
    assert response.status_code == HTTP_201_CREATED, response.json()

    user = await User.by_email("test@test.me")
    assert user.nickname == "test"


async def test_change_password(http_client):
    user = await User.create_user(email="test@test.me", nickname="test", password="asdf")

    token = encode_jwt_token(
        {
            "sub": "test@test.me",
            "id": str(user.id),
            "iat": datetime.now(timezone.utc),
            "exp": datetime.now(timezone.utc) + timedelta(hours=1),
        },
    )

    response = await http_client.post(
        "/change-password", json={"password": "ASDF"}, headers={"Authorization": f"Bearer {token}"}
    )
    assert response.status_code == HTTP_201_CREATED, response.json()

    response = await http_client.post("/login", json={"email": "test@test.me", "password": "asdf"})
    assert response.status_code == HTTP_401_UNAUTHORIZED, response.json()

    response = await http_client.post("/login", json={"email": "test@test.me", "password": "ASDF"})
    assert response.status_code == HTTP_201_CREATED, response.json()
