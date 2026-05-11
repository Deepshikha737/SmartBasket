from fastapi import APIRouter, HTTPException

from app.api.deps import DbDep
from app.models.schemas import RebuildIndexResponse
from app.services.embedding_pipeline import rebuild_faiss_from_db

router = APIRouter(prefix="/api/admin", tags=["admin"])


@router.post("/rebuild-index", response_model=RebuildIndexResponse)
async def rebuild_index(db: DbDep):
    try:
        n, dim = await rebuild_faiss_from_db(db)
    except Exception as e:
        raise HTTPException(500, str(e)) from e
    if n == 0:
        return RebuildIndexResponse(vectors=0, dimension=0, message="No products to index.")
    return RebuildIndexResponse(
        vectors=n,
        dimension=dim,
        message="FAISS index rebuilt and persisted.",
    )
