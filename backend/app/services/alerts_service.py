from datetime import datetime, timezone
from typing import Any

from bson import ObjectId
from motor.motor_asyncio import AsyncIOMotorDatabase

from app.models.schemas import PriceAlertCreate, PriceAlertOut


async def create_alert(db: AsyncIOMotorDatabase, body: PriceAlertCreate) -> PriceAlertOut:
    col = db["price_alerts"]
    now = datetime.now(timezone.utc)
    base = {
        "user_id": body.user_id,
        "product_id": body.product_id,
        "target_price": body.target_price,
        "direction": body.direction,
        "active": True,
        "last_triggered_at": None,
    }
    await col.update_one(
        {"user_id": body.user_id, "product_id": body.product_id},
        {
            "$set": base,
            "$setOnInsert": {"created_at": now},
        },
        upsert=True,
    )
    cur = await col.find_one({"user_id": body.user_id, "product_id": body.product_id})
    assert cur
    return _serialize_alert(cur)


def _serialize_alert(doc: dict[str, Any]) -> PriceAlertOut:
    d = dict(doc)
    d["_id"] = str(d.pop("_id"))
    return PriceAlertOut.model_validate(d)


async def list_alerts(db: AsyncIOMotorDatabase, user_id: str) -> list[PriceAlertOut]:
    col = db["price_alerts"]
    cursor = col.find({"user_id": user_id, "active": True})
    return [_serialize_alert(a) async for a in cursor]


async def check_alerts_once(db: AsyncIOMotorDatabase) -> list[dict[str, Any]]:
    """Return triggered events (for logging / future webhook)."""
    products = db["products"]
    alerts = db["price_alerts"]
    triggered: list[dict[str, Any]] = []
    cursor = alerts.find({"active": True})
    async for alert in cursor:
        pid = alert["product_id"]
        try:
            oid = ObjectId(pid)
        except Exception:
            continue
        p = await products.find_one({"_id": oid})
        if not p:
            continue
        price = float(p["price"])
        target = float(alert["target_price"])
        direction = alert.get("direction", "below")
        fire = False
        if direction == "below" and price <= target:
            fire = True
        elif direction == "any_drop":
            # Compare to price at alert creation — stored optional baseline
            baseline = alert.get("baseline_price")
            if baseline is not None and price < float(baseline) * 0.98:
                fire = True
        if fire:
            await alerts.update_one(
                {"_id": alert["_id"]},
                {"$set": {"last_triggered_at": datetime.now(timezone.utc)}},
            )
            triggered.append(
                {
                    "user_id": alert["user_id"],
                    "product_id": pid,
                    "current_price": price,
                    "target_price": target,
                }
            )
    return triggered


async def ensure_alert_baselines(db: AsyncIOMotorDatabase) -> None:
    products = db["products"]
    alerts = db["price_alerts"]
    async for alert in alerts.find({"active": True, "baseline_price": {"$exists": False}}):
        try:
            p = await products.find_one({"_id": ObjectId(alert["product_id"])})
        except Exception:
            continue
        if p:
            await alerts.update_one(
                {"_id": alert["_id"]},
                {"$set": {"baseline_price": float(p["price"])}},
            )
