from typing import Optional

from fastapi import APIRouter, HTTPException, Query

from app.api.deps import DbDep
from app.models.schemas import ProductOut, SyncResponse
from app.services.ecommerce import ALL_ADAPTERS
from app.services.matching import assign_match_groups
from app.services.product_repository import ProductRepository

router = APIRouter(prefix="/api/products", tags=["products"])


@router.get("", response_model=list[ProductOut])
async def list_products(
    db: DbDep,
    skip: int = 0,
    limit: int = 50,
    category: Optional[str] = None,
):
    repo = ProductRepository(db)
    await repo.ensure_indexes()
    return await repo.list_products(skip=skip, limit=limit, category=category)


@router.get("/{product_id}", response_model=ProductOut)
async def get_product(product_id: str, db: DbDep):
    repo = ProductRepository(db)
    p = await repo.get(product_id)
    if not p:
        raise HTTPException(404, "Product not found")
    return p


@router.post("/sync", response_model=SyncResponse)
async def sync_from_vendors(
    db: DbDep,
    query: Optional[str] = Query(None, description="Optional search query for catalog fetch"),
    limit_per_vendor: int = Query(20, ge=1, le=100),
):
    repo = ProductRepository(db)
    await repo.ensure_indexes()
    inserted = 0
    updated = 0
    sources: list[str] = []
    for adapter in ALL_ADAPTERS:
        sources.append(adapter.name)
        items = await adapter.fetch_products(query=query, limit=limit_per_vendor)
        for p in items:
            existed = await db["products"].find_one({"source": p.source, "external_id": p.external_id})
            await repo.upsert_product(p)
            if existed:
                updated += 1
            else:
                inserted += 1
    n_matched = await assign_match_groups(db)
    return SyncResponse(
        inserted=inserted,
        updated=updated,
        sources=sources,
        message=f"Upserted {inserted + updated} rows ({inserted} new, {updated} updates). "
        f"Match groups touched {n_matched} rows.",
    )
