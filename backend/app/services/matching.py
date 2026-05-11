"""
Cross-vendor product matching: canonical SKU when present, else high SBERT similarity.
"""

from collections import defaultdict
from typing import Any

from bson import ObjectId
from motor.motor_asyncio import AsyncIOMotorDatabase

from app.ai.embeddings import encode_texts, product_to_text
from app.ai.faiss_store import get_faiss_store


async def assign_match_groups(db: AsyncIOMotorDatabase, similarity_threshold: float = 0.82) -> int:
    col = db["products"]
    cursor = col.find({})
    products: list[dict[str, Any]] = [p async for p in cursor]
    sku_groups: dict[str, list[str]] = defaultdict(list)
    no_sku: list[dict[str, Any]] = []
    for p in products:
        pid = str(p["_id"])
        sku = p.get("canonical_sku")
        if sku:
            sku_groups[sku].append(pid)
        else:
            no_sku.append(p)

    updated = 0
    for sku, ids in sku_groups.items():
        gid = f"sku:{sku}"
        for pid in ids:
            await col.update_one({"_id": ObjectId(pid)}, {"$set": {"matched_group_id": gid}})
            updated += 1

    if not no_sku:
        return updated

    texts = [
        product_to_text(p.get("title", ""), p.get("description", ""), p.get("category", ""), p.get("brand"))
        for p in no_sku
    ]
    ids = [str(p["_id"]) for p in no_sku]
    emb = encode_texts(texts)
    import numpy as np

    sim = np.matmul(emb, emb.T)
    parent = list(range(len(ids)))

    def find(i: int) -> int:
        while parent[i] != i:
            parent[i] = parent[parent[i]]
            i = parent[i]
        return i

    def union(a: int, b: int) -> None:
        ra, rb = find(a), find(b)
        if ra != rb:
            parent[rb] = ra

    n = len(ids)
    for i in range(n):
        for j in range(i + 1, n):
            if sim[i, j] >= similarity_threshold:
                union(i, j)

    clusters: dict[int, list[int]] = defaultdict(list)
    for i in range(n):
        clusters[find(i)].append(i)

    cluster_num = 0
    for members in clusters.values():
        cluster_num += 1
        gid = f"emb:{cluster_num}"
        for idx in members:
            pid = ids[idx]
            await col.update_one({"_id": ObjectId(pid)}, {"$set": {"matched_group_id": gid}})
            updated += 1

    return updated


def faiss_ready() -> bool:
    return get_faiss_store().ready
