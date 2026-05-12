import logging
from typing import Any

import numpy as np
from motor.motor_asyncio import AsyncIOMotorDatabase

from app.ai.embeddings import encode_texts, product_to_text
from app.ai.faiss_store import get_faiss_store
from app.services.ecommerce.allowed_sources import is_allowed_source

_log = logging.getLogger(__name__)


async def rebuild_faiss_from_db(db: AsyncIOMotorDatabase) -> tuple[int, int]:
    col = db["products"]
    cursor = col.find({})
    docs: list[dict[str, Any]] = [d async for d in cursor if is_allowed_source(d.get("source"))]
    if not docs:
        _log.warning("No products in DB; skipping FAISS build.")
        return 0, 0

    texts = [
        product_to_text(d.get("title", ""), d.get("description", ""), d.get("category", ""), d.get("brand"))
        for d in docs
    ]
    emb = encode_texts(texts)
    ids = [str(d["_id"]) for d in docs]
    store = get_faiss_store()
    store.build(emb, ids)
    store.persist()
    dim = emb.shape[1]
    await col.update_many({}, {"$set": {"embedding_version": 1}})
    _log.info("FAISS rebuilt: %s vectors, dim=%s", len(ids), dim)
    return len(ids), dim
