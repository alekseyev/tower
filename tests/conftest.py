from datetime import datetime, timedelta, timezone
import pytest
import pytest_asyncio
from httpx import AsyncClient
from testcontainers.mongodb import MongoDbContainer

from backend.api_app import app
from backend.app_ctx import AppCtx
from backend.babble.models import BabbleSentence
from backend.core.crypto import encode_jwt_token
from backend.core.models import User
from backend.settings import settings


@pytest.fixture(autouse=True)
def autouse_fixtures(app_ctx, clean_db):
    pass


@pytest.fixture(scope="session")
def mongo_container():
    with MongoDbContainer() as mongo_container:
        yield mongo_container


@pytest_asyncio.fixture
async def app_ctx(mongo_container, http_client):
    settings.MONGO_URL = mongo_container.get_connection_url()
    await AppCtx.start()
    yield AppCtx
    await AppCtx.shutdown()


@pytest_asyncio.fixture()
async def clean_db():
    await User.find_all().delete()
    await BabbleSentence.find_all().delete()


@pytest_asyncio.fixture
async def http_client():
    async with AsyncClient(app=app, base_url="http://test") as client:
        yield client


@pytest_asyncio.fixture
async def user():
    return await User.create_user(email="test@test.me", nickname="test", password="asdf")


@pytest.fixture
def auth_headers(user):
    token = encode_jwt_token(
        {
            "sub": user.email,
            "id": str(user.id),
            "iat": datetime.now(timezone.utc),
            "exp": datetime.now(timezone.utc) + timedelta(hours=1),
        },
    )
    return {"Authorization": f"Bearer {token}"}
