from motor.motor_asyncio import AsyncIOMotorClient
from pymongo.errors import ConnectionFailure
from app.config import MONGODB_URI, MONGODB_DB_NAME

client: AsyncIOMotorClient = None


async def get_db() -> AsyncIOMotorClient:
    """Get the MongoDB client."""
    global client
    if client is None:
        client = AsyncIOMotorClient(MONGODB_URI)
    return client


async def get_database():
    """Get the database instance."""
    database_client = await get_db()
    return database_client[MONGODB_DB_NAME]


async def get_collection() -> AsyncIOMotorClient:
    """Get the calls collection."""
    return (await get_db())[MONGODB_DB_NAME]["calls"]


async def create_indexes() -> None:
    """Create indexes required for webhook idempotency and history queries."""
    database = await get_database()
    await database["calls"].create_index("retell_call_id", unique=True)
    await database["calls"].create_index([("profile_id", 1), ("created_at", -1)])
    await database["profiles"].create_index("created_at")


async def check_mongodb_connection() -> bool:
    """Check MongoDB connectivity."""
    try:
        client = await get_db()
        await client.admin.command("ping")
        return True
    except ConnectionFailure:
        return False
    except Exception:
        return False


async def close_db_connection():
    """Close the MongoDB client connection."""
    global client
    if client is not None:
        client.close()
        client = None
