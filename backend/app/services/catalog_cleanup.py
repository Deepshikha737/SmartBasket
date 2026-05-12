import logging

from bson import ObjectId
from motor.motor_asyncio import AsyncIOMotorDatabase

from app.services.ecommerce.allowed_sources import ALLOWED_PRODUCT_SOURCES

_log = logging.getLogger(__name__)


async def clear_all_product_listings(db: AsyncIOMotorDatabase) -> int:
    """
    Remove every product row and its price_history so the next ingest reflects
    only the current search (no carry-over from prior searches).
    """
    col = db["products"]
    hist = db["price_history"]
    id_strs = [str(doc["_id"]) async for doc in col.find({}, {"_id": 1})]
    if id_strs:
        await hist.delete_many({"product_id": {"$in": id_strs}})
    res = await col.delete_many({})
    n = int(res.deleted_count or 0)
    if n:
        _log.info("Cleared %s product listing(s) for a fresh search.", n)
    return n


async def purge_disallowed_products(db: AsyncIOMotorDatabase) -> int:
    """
    Delete products (and their price_history) whose `source` is not in ALLOWED_PRODUCT_SOURCES.
    Removes legacy rows (e.g. shopalpha, betamart) so they never appear in search or FAISS.
    """
    col = db["products"]
    hist = db["price_history"]
    allowed = list(ALLOWED_PRODUCT_SOURCES)
    cursor = col.find({"source": {"$nin": allowed}}, {"_id": 1})
    oids: list[ObjectId] = []
    id_strs: list[str] = []
    async for doc in cursor:
        oids.append(doc["_id"])
        id_strs.append(str(doc["_id"]))
    if not oids:
        return 0
    await hist.delete_many({"product_id": {"$in": id_strs}})
    res = await col.delete_many({"_id": {"$in": oids}})
    n = int(res.deleted_count or 0)
    if n:
        _log.info("Purged %s non-allowed product listing(s) from catalog.", n)
    return n
