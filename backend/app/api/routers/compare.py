from statistics import mean

from fastapi import APIRouter, HTTPException

from app.api.deps import DbDep
from app.models.schemas import CompareRequest
from app.services.product_repository import ProductRepository

router = APIRouter(prefix="/api/compare", tags=["compare"])


@router.post("")
async def compare_products(body: CompareRequest, db: DbDep):
    repo = ProductRepository(db)
    products = await repo.get_many(body.product_ids)
    if len(products) < 2:
        raise HTTPException(400, "Need at least two valid product IDs")
    prices = [p.price for p in products]
    ratings = [p.rating for p in products if p.rating is not None]
    best_price = min(products, key=lambda x: x.price)
    best_rating = max(products, key=lambda x: (x.rating or 0, x.review_count))
    return {
        "products": [p.model_dump() for p in products],
        "summary": {
            "price_min": min(prices),
            "price_max": max(prices),
            "price_spread_pct": round((max(prices) - min(prices)) / max(prices) * 100, 2) if max(prices) else 0,
            "avg_rating": round(mean(ratings), 2) if ratings else None,
            "best_price_product_id": best_price.id,
            "best_rating_product_id": best_rating.id,
        },
    }
