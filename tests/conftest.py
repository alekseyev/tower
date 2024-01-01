import asyncio

import pytest
import pytest_asyncio
from testcontainers.mongodb import MongoDbContainer

from app.app_ctx import AppCtx
from app.data_layer.models import BabbleSentence
from app.settings import settings


@pytest.fixture(autouse=True)
def autouse_fixtures(app_ctx, clean_db):
    pass


@pytest.fixture(scope="session")
def event_loop():
    loop = asyncio.get_event_loop()
    yield loop
    loop.close()


@pytest_asyncio.fixture(scope="session")
async def app_ctx(event_loop):
    with MongoDbContainer() as mongo_container:
        settings.MONGO_URL = mongo_container.get_connection_url()
        await AppCtx.start()
        yield AppCtx
        await AppCtx.shutdown()


@pytest_asyncio.fixture()
async def clean_db():
    await BabbleSentence.find_all().delete()
