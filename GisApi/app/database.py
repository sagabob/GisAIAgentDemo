import logging

from motor.motor_asyncio import AsyncIOMotorClient, AsyncIOMotorCollection

from app.config import Settings

logger = logging.getLogger(__name__)


async def ensure_indexes(client: AsyncIOMotorClient, settings: Settings) -> None:
    poi_collection = client[settings.db_name][settings.demo_collection_name]
    await poi_collection.create_index("placeNameId", unique=True, name="uniq_placeNameId")
    logger.info("Ensured unique index on %s.placeNameId", settings.demo_collection_name)


async def ping_database(client: AsyncIOMotorClient) -> None:
    await client.admin.command("ping")
