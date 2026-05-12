from typing import Any, Optional

from motor.motor_asyncio import AsyncIOMotorDatabase

from app.ai.embeddings import encode_texts, product_to_text
from app.ai.faiss_store import get_faiss_store
from app.models.schemas import ProductOut
from app.services.ecommerce.allowed_sources import is_allowed_source
from app.services.product_repository import ProductRepository


async def load_user_prefs(db: AsyncIOMotorDatabase, user_id: Optional[str]) -> dict[str, Any]:
    if not user_id:
        return {}
    doc = await db["user_preferences"].find_one({"user_id": user_id})
    return dict(doc) if doc else {}


async def recommend_for_product(
    db: AsyncIOMotorDatabase,
    product_id: str,
    user_id: Optional[str],
    top_k: int = 8,
) -> dict[str, Any]:
    repo = ProductRepository(db)
    anchor = await repo.get(product_id)
    if not anchor or not is_allowed_source(anchor.source):
        return {"error": "product not found", "similar": [], "cheaper": [], "premium": [], "similar_models": []}

    prefs = await load_user_prefs(db, user_id)
    max_price = prefs.get("max_price")
    min_rating = prefs.get("min_rating")
    cats = set(prefs.get("preferred_categories") or [])

    text = product_to_text(anchor.title, anchor.description, anchor.category, anchor.brand)
    q = encode_texts([text])
    store = get_faiss_store()
    hits = store.search(q[0], top_k=top_k * 6)
    id_scores = {pid: s for pid, s in hits if pid != anchor.id}
    if not id_scores:
        return {"anchor": anchor.model_dump(), "similar": [], "cheaper": [], "premium": [], "similar_models": []}

    products = await repo.list_by_ids_str(list(id_scores.keys()))

    items: list[tuple[ProductOut, float]] = []
    for pid, sc in id_scores.items():
        p = products.get(pid)
        if not p or not is_allowed_source(p.source):
            continue
        if cats and p.category not in cats:
            continue
        if min_rating is not None and (p.rating or 0) < min_rating:
            continue
        if max_price is not None and p.price > max_price:
            continue
        items.append((p, sc))

    items.sort(key=lambda x: -x[1])
    similar = [_dump(p, s) for p, s in items[:top_k]]

    cheaper_pool = [p for p, _ in items if p.price < anchor.price * 0.95]
    cheaper_pool.sort(key=lambda x: x.price)
    cheaper = [_dump(p, id_scores.get(p.id, 0.0)) for p in cheaper_pool[:top_k]]

    premium_pool = [p for p, _ in items if p.price > anchor.price * 1.05]
    premium_pool.sort(key=lambda x: -x.price)
    premium = [_dump(p, id_scores.get(p.id, 0.0)) for p in premium_pool[:top_k]]

    anchor_brand = (anchor.brand or "").strip().lower()
    cross_brand = [
        (p, s)
        for p, s in items
        if (p.brand or "").strip().lower() != anchor_brand and p.category == anchor.category
    ]
    cross_brand.sort(key=lambda x: -x[1])
    similar_models = [_dump(p, s) for p, s in cross_brand[:top_k]]

    return {
        "anchor": anchor.model_dump(),
        "similar": similar,
        "cheaper": cheaper,
        "premium": premium,
        "similar_models": similar_models,
    }


def _dump(p: Any, similarity: float) -> dict[str, Any]:
    d = p.model_dump()
    d["similarity"] = round(float(similarity), 4)
    return d
