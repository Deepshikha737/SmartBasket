from fastapi import APIRouter

from app.ai.faiss_store import get_faiss_store

router = APIRouter(tags=["health"])


@router.get("/health")
async def health():
    return {"status": "ok", "faiss_ready": get_faiss_store().ready}
