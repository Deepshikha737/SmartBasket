import logging
from collections import defaultdict
from typing import Any, Optional

from motor.motor_asyncio import AsyncIOMotorDatabase

from app.ai.embeddings import encode_texts
from app.ai.faiss_store import get_faiss_store
from app.ai.sentiment import analyze_batch
from app.models.schemas import (
    ComparedListing,
    ListingScoreBreakdown,
    ProductGroupResult,
    ProductOut,
    UnifiedSearchResponse,
)
from app.services.best_store import build_recommendation_sentence, pick_best, score_listing
from app.services.ecommerce import ALL_ADAPTERS
from app.services.embedding_pipeline import rebuild_faiss_from_db
from app.services.matching import assign_match_groups
from app.services.product_repository import ProductRepository
from app.services.purchase_insights import (
    best_delivery_platform,
    best_overall_platform,
    best_price_platform,
    build_store_rollups,
    group_award_rationale,
    listing_trust_index,
    session_final_recommendation,
)
from app.services.recommender import recommend_for_product

_log = logging.getLogger(__name__)


def _sentiment_positive_ratio(reviews: list[str]) -> tuple[float, int]:
    if not reviews:
        return 0.5, 0
    raw = analyze_batch(reviews[:24])
    pos = 0
    for r in raw:
        lab = str(r.get("label", "")).upper()
        if lab == "POSITIVE" or lab.endswith("POSITIVE"):
            pos += 1
    ratio = pos / max(1, len(raw))
    return ratio, len(raw)


async def run_unified_search(
    db: AsyncIOMotorDatabase,
    query: str,
    limit_per_vendor: int = 20,
    rebuild_index: bool = True,
    semantic_top_k: int = 40,
) -> UnifiedSearchResponse:
    repo = ProductRepository(db)
    await repo.ensure_indexes()

    sources: list[str] = []
    for adapter in ALL_ADAPTERS:
        sources.append(adapter.name)
        items = await adapter.fetch_products(query=query, limit=limit_per_vendor)
        for p in items:
            await repo.upsert_product(p)

    n_match = await assign_match_groups(db)
    sync_note = f"Queried Amazon, Flipkart, Croma, Meesho ({len(sources)} sources). Semantic matching updated {n_match} rows."

    if rebuild_index:
        n_vec, _dim = await rebuild_faiss_from_db(db)
        sync_note += f" FAISS index rebuilt ({n_vec} vectors)."
    else:
        store = get_faiss_store()
        if not store.ready:
            await rebuild_faiss_from_db(db)
            sync_note += " FAISS was missing — rebuilt."

    cand: set[str] = set()
    store = get_faiss_store()
    if store.ready:
        qv = encode_texts([query.strip()])[0]
        for pid, sc in store.search(qv, top_k=semantic_top_k):
            cand.add(pid)

    rx = {"$regex": query.strip(), "$options": "i"}
    async for d in db["products"].find({"$or": [{"title": rx}, {"description": rx}]}).limit(80):
        cand.add(str(d["_id"]))

    if not cand:
        return UnifiedSearchResponse(
            query=query,
            sources_queried=sources,
            groups=[],
            alternatives={},
            sync_note=sync_note + " No candidates for this query.",
            store_sentiment_rollups=[],
            final_ai_recommendation=session_final_recommendation([]),
        )

    group_to_products: dict[str, list[ProductOut]] = defaultdict(list)
    seen_group: set[str] = set()

    for pid in cand:
        p = await repo.get(pid)
        if not p:
            continue
        gid = p.matched_group_id or f"solo:{p.id}"
        if gid in seen_group:
            continue
        seen_group.add(gid)
        if gid.startswith("solo:"):
            group_to_products[gid] = [p]
        else:
            cursor = db["products"].find({"matched_group_id": gid})
            grp: list[ProductOut] = []
            async for doc in cursor:
                doc["_id"] = str(doc["_id"])
                rev = doc.get("reviews") or []
                doc["reviews_sample"] = rev[:5]
                doc.pop("reviews", None)
                doc.pop("embedding", None)
                doc.setdefault("delivery_days", 5)
                doc.setdefault("delivery_text", "")
                doc.setdefault("free_shipping", False)
                grp.append(ProductOut.model_validate(doc))
            if grp:
                group_to_products[gid] = grp

    sem_scores: dict[str, float] = {}
    if store.ready:
        qv = encode_texts([query.strip()])[0]
        hits = {pid: sc for pid, sc in store.search(qv, top_k=semantic_top_k)}
        for gid, plist in group_to_products.items():
            mx = max((hits.get(x.id, 0.0) for x in plist), default=0.0)
            if mx > 0:
                sem_scores[gid] = float(mx)

    groups_out: list[ProductGroupResult] = []
    all_listings_flat: list[ComparedListing] = []
    session_tuples: list[tuple[str, Optional[str], Optional[str], Optional[str]]] = []
    anchor_for_alt: Optional[ProductOut] = None

    for gid, plist in sorted(group_to_products.items(), key=lambda x: -sem_scores.get(x[0], 0.0)):
        prices = [x.price for x in plist]
        rows_scored: list[tuple[ProductOut, ListingScoreBreakdown, ComparedListing]] = []

        for prod in plist:
            full_reviews = await repo.get_reviews(prod.id, max_n=30)
            pos_ratio, nrev = _sentiment_positive_ratio(full_reviews)
            neg_ratio = round(1.0 - pos_ratio, 4)
            bd = score_listing(prod, pos_ratio, prices)
            rating = prod.rating
            trust = listing_trust_index(pos_ratio, nrev, rating)
            cl = ComparedListing(
                product=prod.model_dump(),
                sentiment_positive_ratio=round(pos_ratio, 4),
                sentiment_negative_ratio=neg_ratio,
                sentiment_review_count=nrev,
                trust_index=trust,
                score_breakdown=bd,
                price_prediction_lstm=None,
                price_prediction_xgb=None,
            )
            rows_scored.append((prod, bd, cl))
            all_listings_flat.append(cl)

        listings = [t[2] for t in rows_scored]
        ranked = [(p, b) for p, b, _ in rows_scored]
        best_pick = pick_best(ranked)
        best_id, best_src = (best_pick[0], best_pick[1]) if best_pick else (None, None)
        best_prod = next((p for p in plist if p.id == best_id), None)
        others = [p for p in plist if p.id != best_id]
        best_bd = next((b for p, b, _ in rows_scored if p.id == best_id), None)
        summary = (
            build_recommendation_sentence(best_prod, others, best_bd)
            if best_prod and best_bd
            else "Insufficient data to rank."
        )

        bp_store = best_price_platform(listings)
        bd_store = best_delivery_platform(listings)
        bo_store = best_overall_platform(listings)

        display = plist[0].title[:80] if plist else gid
        if len(plist) > 1 and best_prod:
            display = f"{best_prod.title[:60]} ({len(plist)} platforms)"

        session_tuples.append((display, bo_store, bp_store, bd_store))

        groups_out.append(
            ProductGroupResult(
                group_id=gid,
                display_name=display,
                semantic_match_score=round(sem_scores.get(gid, 0.0), 4) if gid in sem_scores else None,
                listings=listings,
                best_listing_product_id=best_id,
                best_store=best_src,
                recommendation_summary=summary,
                best_price_store=bp_store,
                best_overall_store=bo_store,
                best_delivery_store=bd_store,
                best_price_rationale=group_award_rationale("price", bp_store or "", listings)
                if bp_store
                else "",
                best_delivery_rationale=group_award_rationale("delivery", bd_store or "", listings)
                if bd_store
                else "",
                best_overall_rationale=group_award_rationale("overall", bo_store or "", listings)
                if bo_store
                else "",
            )
        )

        if anchor_for_alt is None and best_prod:
            anchor_for_alt = best_prod

    rollups = build_store_rollups(all_listings_flat)
    final_ai = session_final_recommendation(session_tuples)

    alternatives: dict[str, Any] = {}
    if anchor_for_alt and store.ready:
        try:
            alternatives = await recommend_for_product(db, anchor_for_alt.id, user_id=None, top_k=6)
        except Exception as e:
            _log.warning("Alternatives failed: %s", e)
            alternatives = {"error": str(e)}

    return UnifiedSearchResponse(
        query=query,
        sources_queried=sources,
        groups=groups_out,
        alternatives=alternatives,
        sync_note=sync_note,
        store_sentiment_rollups=rollups,
        final_ai_recommendation=final_ai,
    )
