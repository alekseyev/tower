from motor.motor_asyncio import AsyncIOMotorClient, AsyncIOMotorDatabase


def get_mongo_db(url: str, db: str) -> AsyncIOMotorDatabase:
    db = AsyncIOMotorClient(url)[db]
    return db
