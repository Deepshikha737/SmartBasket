from datetime import datetime, timezone
from typing import Any, Optional

from bson import ObjectId
from motor.motor_asyncio import AsyncIOMotorDatabase
from pymongo import ReturnDocument

from app.models.schemas import ProductCreate, ProductOut


def _serialize(doc: dict[str, Any]) -> ProductOut:
    d = dict(doc)
    d["_id"] = str(d.pop("_id"))
    rev = d.get("reviews") or []
    d["reviews_sample"] = rev[:5]
    d.pop("reviews", None)
    d.pop("embedding", None)
    d.setdefault("delivery_days", 5)
    d.setdefault("delivery_text", "")
    d.setdefault("free_shipping", False)
    return ProductOut.model_validate(d)


class ProductRepository:
    def __init__(self, db: AsyncIOMotorDatabase):
        self._col = db["products"]
        self._history = db["price_history"]
        self._db = db

    async def ensure_indexes(self) -> None:
        await self._col.create_index([("source", 1), ("external_id", 1)], unique=True)
        await self._col.create_index("canonical_sku")
        await self._col.create_index("matched_group_id")
        try:
            await self._col.create_index([("title", "text"), ("description", "text")])
        except Exception:
            pass
        await self._history.create_index([("product_id", 1), ("ts", -1)])

    async def upsert_product(self, p: ProductCreate) -> str:
        now = datetime.now(timezone.utc)
        doc = p.model_dump()
        doc["updated_at"] = now
        prev = await self._col.find_one_and_update(
            {"source": p.source, "external_id": p.external_id},
            {
                "$set": doc,
                "$setOnInsert": {"created_at": now},
            },
            upsert=True,
            return_document=ReturnDocument.AFTER,
        )
        pid = str(prev["_id"]) if prev and "_id" in prev else None
        if pid is None:
            cur = await self._col.find_one({"source": p.source, "external_id": p.external_id})
            pid = str(cur["_id"]) if cur else ""
        await self._history.insert_one({"product_id": pid, "price": p.price, "ts": now})
        return pid

    async def get(self, product_id: str) -> Optional[ProductOut]:
        doc = await self._col.find_one({"_id": ObjectId(product_id)})
        return _serialize(doc) if doc else None

    async def get_many(self, ids: list[str]) -> list[ProductOut]:
        oids = []
        for i in ids:
            try:
                oids.append(ObjectId(i))
            except Exception:
                continue
        cursor = self._col.find({"_id": {"$in": oids}})
        return [_serialize(d) async for d in cursor]

    async def list_products(self, skip: int = 0, limit: int = 50, category: Optional[str] = None) -> list[ProductOut]:
        q: dict[str, Any] = {}
        if category:
            q["category"] = category
        cursor = self._col.find(q).sort("updated_at", -1).skip(skip).limit(limit)
        return [_serialize(d) async for d in cursor]

    async def text_search(self, q: str, limit: int = 20) -> list[ProductOut]:
        cursor = self._col.find({"$text": {"$search": q}}).limit(limit)
        return [_serialize(d) async for d in cursor]

    async def all_for_embedding(self) -> list[dict[str, Any]]:
        cursor = self._col.find({}, {"title": 1, "description": 1, "category": 1, "brand": 1})
        return [d async for d in cursor]

    async def get_reviews(self, product_id: str, max_n: int = 50) -> list[str]:
        doc = await self._col.find_one({"_id": ObjectId(product_id)}, {"reviews": 1})
        if not doc:
            return []
        return list(doc.get("reviews") or [])[:max_n]

    async def price_series(self, product_id: str, limit: int = 64) -> list[float]:
        cursor = (
            self._history.find({"product_id": product_id}).sort("ts", -1).limit(limit)
        )
        pts = [d["price"] async for d in cursor]
        return list(reversed(pts))

    async def update_match_group(self, product_id: str, group_id: str) -> None:
        await self._col.update_one({"_id": ObjectId(product_id)}, {"$set": {"matched_group_id": group_id}})

    async def list_by_ids_str(self, ids: list[str]) -> dict[str, ProductOut]:
        out = await self.get_many(ids)
        return {p.id: p for p in out}
