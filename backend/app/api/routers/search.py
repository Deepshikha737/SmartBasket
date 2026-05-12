from fastapi import APIRouter, HTTPException, Query

from app.ai.embeddings import encode_texts
from app.ai.faiss_store import get_faiss_store
from app.api.deps import DbDep
from app.models.schemas import ProductOut, SemanticSearchRequest, UnifiedSearchResponse
from app.services.ecommerce.allowed_sources import ALLOWED_PRODUCT_SOURCES, is_allowed_source
from app.services.product_repository import ProductRepository
from app.services.unified_search import run_unified_search

router = APIRouter(prefix="/api/search", tags=["search"])


@router.get("/unified", response_model=UnifiedSearchResponse)
async def unified_product_search(
    db: DbDep,
    q: str = Query(..., min_length=1, max_length=256, description="e.g. iPhone 15, wireless headphones"),
    limit_per_vendor: int = Query(24, ge=4, le=80),
    rebuild_index: bool = Query(True, description="Rebuild FAISS after ingest for semantic grouping"),
):
    """
    End-to-end flow: fetch Amazon, Flipkart, Croma, Meesho for ``q``, upsert, SBERT match groups,
    FAISS rebuild, group same products across stores, score listings (price, rating,
    sentiment, offers, delivery), pick best store, attach similar/cheaper/premium alternatives.
    """
    return await run_unified_search(
        db,
        query=q.strip(),
        limit_per_vendor=limit_per_vendor,
        rebuild_index=rebuild_index,
    )


@router.get("/keyword", response_model=list[ProductOut])
async def keyword_search(db: DbDep, q: str, limit: int = 20):
    repo = ProductRepository(db)
    await repo.ensure_indexes()
    try:
        return await repo.text_search(q, limit=limit)
    except Exception:
        # Fallback if text index missing
        cursor = db["products"].find(
            {
                "$and": [
                    {"$or": [{"title": {"$regex": q, "$options": "i"}}, {"description": {"$regex": q, "$options": "i"}}]},
                    {"source": {"$in": list(ALLOWED_PRODUCT_SOURCES)}},
                ]
            }
        ).limit(limit)
        out = []
        async for d in cursor:
            d["_id"] = str(d["_id"])
            rev = d.get("reviews") or []
            d["reviews_sample"] = rev[:5]
            d.pop("reviews", None)
            d.pop("embedding", None)
            d.setdefault("delivery_days", 5)
            d.setdefault("delivery_text", "")
            d.setdefault("free_shipping", False)
            out.append(ProductOut.model_validate(d))
        return out


@router.post("/semantic", response_model=list[dict])
async def semantic_search(body: SemanticSearchRequest, db: DbDep):
    store = get_faiss_store()
    if not store.ready:
        raise HTTPException(503, "FAISS index not built. POST /api/admin/rebuild-index first.")
    qv = encode_texts([body.query])[0]
    hits = store.search(qv, top_k=body.top_k)
    repo = ProductRepository(db)
    pmap = await repo.list_by_ids_str([pid for pid, _ in hits])
    ranked = []
    for pid, score in hits:
        p = pmap.get(pid)
        if p and is_allowed_source(p.source):
            ranked.append({"product": p.model_dump(), "score": round(float(score), 4)})
    return ranked
