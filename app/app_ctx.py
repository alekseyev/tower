from contextlib import asynccontextmanager

from beanie import init_beanie
from motor.motor_asyncio import AsyncIOMotorClient

from app.data_layer.models import BabbleSentence
from app.settings import settings


class AppCtx:
    mongo_client: AsyncIOMotorClient

    @classmethod
    async def start(cls) -> None:
        cls.mongo_client = AsyncIOMotorClient(settings.MONGO_URL)
        await init_beanie(database=cls.mongo_client[settings.MONGO_DB], document_models=[BabbleSentence])

    @classmethod
    async def shutdown(cls) -> None:
        pass


@asynccontextmanager
async def get_application_ctx():
    await AppCtx.start()
    try:
        yield AppCtx
    finally:
        await AppCtx.shutdown()
