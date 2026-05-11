from typing import Any, AsyncGenerator, Optional

from motor.motor_asyncio import AsyncIOMotorClient, AsyncIOMotorDatabase

from app.config import get_settings

_client: Optional[AsyncIOMotorClient] = None


async def get_client() -> AsyncIOMotorClient:
    global _client
    if _client is None:
        settings = get_settings()
        _client = AsyncIOMotorClient(settings.mongodb_uri)
    return _client


async def get_db() -> AsyncIOMotorDatabase:
    settings = get_settings()
    client = await get_client()
    return client[settings.mongodb_db]


async def close_db() -> None:
    global _client
    if _client is not None:
        _client.close()
        _client = None


async def db_session() -> AsyncGenerator[AsyncIOMotorDatabase, None]:
    db = await get_db()
    try:
        yield db
    finally:
        pass


def ensure_indexes_sync_instructions() -> dict[str, Any]:
    """Run once via script or migration — documented indexes for ops."""
    return {
        "products": [
            {"keys": [("canonical_sku", 1)], "unique": True, "sparse": True},
            {"keys": [("source", 1), ("external_id", 1)], "unique": True},
            {"keys": [("title", "text"), ("description", "text")]},
            {"keys": [("category", 1)]},
            {"keys": [("embedding_version", 1)]},
        ],
        "user_preferences": [{"keys": [("user_id", 1)], "unique": True}],
        "price_alerts": [
            {"keys": [("user_id", 1), ("product_id", 1)], "unique": True},
            {"keys": [("active", 1)]},
        ],
        "price_history": [{"keys": [("product_id", 1), ("ts", -1)]}],
    }
