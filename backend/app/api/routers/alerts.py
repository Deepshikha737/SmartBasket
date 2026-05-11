from bson import ObjectId
from fastapi import APIRouter, HTTPException, Query

from app.api.deps import DbDep
from app.models.schemas import PriceAlertCreate, PriceAlertOut
from app.services.alerts_service import create_alert, list_alerts

router = APIRouter(prefix="/api/alerts", tags=["alerts"])


@router.post("", response_model=PriceAlertOut)
async def add_alert(body: PriceAlertCreate, db: DbDep):
    # ensure product exists
    try:
        oid = ObjectId(body.product_id)
    except Exception:
        raise HTTPException(400, "Invalid product_id") from None
    p = await db["products"].find_one({"_id": oid})
    if not p:
        raise HTTPException(404, "Product not found")
    return await create_alert(db, body)


@router.get("", response_model=list[PriceAlertOut])
async def get_alerts(db: DbDep, user_id: str = Query(...)):
    return await list_alerts(db, user_id)
