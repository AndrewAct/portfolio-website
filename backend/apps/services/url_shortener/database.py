from motor.motor_asyncio import AsyncIOMotorClient
from pymongo import IndexModel, ASCENDING
from ...config import get_settings

settings = get_settings()

# Create MongoDB client
client = AsyncIOMotorClient(settings.mongodb_url)
database = client[settings.mongodb_database]
url_collection = database.urls


async def init_db():
    # Create indexes for faster queries
    await url_collection.create_indexes([
        IndexModel([("short_url", ASCENDING)], unique=True),
        IndexModel([("original_url", ASCENDING)])
    ])


async def close_db():
    client.close()


def get_collection():
    """Get URL collection"""
    return url_collection
