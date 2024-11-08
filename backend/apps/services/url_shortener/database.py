from motor.motor_asyncio import AsyncIOMotorClient
from pymongo import IndexModel, ASCENDING
import certifi
from ...config import get_settings

settings = get_settings()

# Create MongoDB client with updated SSL/TLS configuration
client = AsyncIOMotorClient(
    settings.mongodb_url,
    tlsCAFile=certifi.where(),  # Explicitly specify the CA file
    serverSelectionTimeoutMS=5000
)


# Verify the connection
try:
    # The ismaster command is cheap and does not require auth.
    client.admin.command('ismaster')
except Exception as e:
    print(f"Failed to connect to MongoDB: {e}")
    raise

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
