from fastapi import APIRouter, HTTPException

from app.api.deps import DbDep
from app.models.schemas import RecommendationRequest, UserPreferences
from app.services.recommender import recommend_for_product

router = APIRouter(prefix="/api/recommendations", tags=["recommendations"])


@router.post("")
async def recommendations(body: RecommendationRequest, db: DbDep):
    data = await recommend_for_product(db, body.product_id, body.user_id, top_k=body.top_k)
    if data.get("error"):
        raise HTTPException(404, data["error"])
    return data


@router.put("/preferences")
async def upsert_preferences(prefs: UserPreferences, db: DbDep):
    col = db["user_preferences"]
    doc = prefs.model_dump()
    await col.update_one({"user_id": prefs.user_id}, {"$set": doc}, upsert=True)
    return {"ok": True, "user_id": prefs.user_id}
