from contextlib import asynccontextmanager

from motor.motor_asyncio import AsyncIOMotorDatabase

from app.data_layer.connections import get_mongo_db
from app.settings import settings


class AppCtx:
    mongo_db: AsyncIOMotorDatabase

    @classmethod
    async def start(cls) -> None:
        cls.mongo_db = get_mongo_db(url=settings.MONGO_URL, db=settings.MONGO_DB)

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
