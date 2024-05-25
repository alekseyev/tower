from contextlib import asynccontextmanager

from beanie import init_beanie
from litestar import Litestar
from motor.motor_asyncio import AsyncIOMotorClient

from backend.babble.models import babble_models
from backend.core.models import core_models
from backend.courses.models import courses_models
from backend.settings import settings


class AppCtx:
    mongo_client: AsyncIOMotorClient

    @classmethod
    async def start(cls) -> None:
        cls.mongo_client = AsyncIOMotorClient(settings.MONGO_URL)
        await init_beanie(
            database=cls.mongo_client[settings.MONGO_DB],
            document_models=[*babble_models, *core_models, *courses_models],
        )

    @classmethod
    async def shutdown(cls) -> None:
        pass


@asynccontextmanager
async def get_application_ctx(app: Litestar | None = None):
    app_ctx = None
    if app:
        app_ctx = getattr(app.state, "app_ctx", None)

    if not app_ctx:
        app_ctx = AppCtx()
        await app_ctx.start()

        if app:
            app.state.app_ctx = app_ctx

    try:
        yield app_ctx
    finally:
        await app_ctx.shutdown()
