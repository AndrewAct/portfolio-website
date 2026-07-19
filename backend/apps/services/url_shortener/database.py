import certifi
from pymongo import ASCENDING, AsyncMongoClient, IndexModel
from pymongo.server_api import ServerApi

from ...config import get_settings

settings = get_settings()

# Create MongoDB client with updated SSL/TLS configuration
client = AsyncMongoClient(
    settings.mongodb_url,
    server_api=ServerApi("1"),
    tlsCAFile=certifi.where(),  # Explicitly specify the CA file
    serverSelectionTimeoutMS=5000,
)


database = client[settings.mongodb_database]
url_collection = database.urls


async def init_db():
    # The first awaited operation also verifies the MongoDB connection.
    await url_collection.create_indexes(
        [
            IndexModel([("short_url", ASCENDING)], unique=True),
            IndexModel([("original_url", ASCENDING)]),
        ]
    )


async def close_db():
    await client.close()


def get_collection():
    """Get URL collection"""
    return url_collection
