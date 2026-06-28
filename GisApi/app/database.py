from motor.motor_asyncio import AsyncIOMotorClient, AsyncIOMotorCollection

from app.config import get_collection_name, get_db_name, get_mongo_uri

_client: AsyncIOMotorClient | None = None


def get_collection(collection_name: str | None = None) -> AsyncIOMotorCollection:
    global _client

    if _client is None:
        _client = AsyncIOMotorClient(get_mongo_uri())

    name = collection_name or get_collection_name()
    return _client[get_db_name()][name]


async def close_client() -> None:
    global _client
    if _client is not None:
        _client.close()
        _client = None
