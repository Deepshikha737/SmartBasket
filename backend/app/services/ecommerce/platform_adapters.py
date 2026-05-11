"""
Platform adapters: Amazon, Flipkart, Croma, and Meesho.

Each adapter implements `fetch_products` for one retailer. Wire real catalogue APIs
(SP-API, Flipkart affiliate, Croma partner, Meesho seller tools, etc.) inside
`fetch_products` while keeping the same `ProductCreate` contract and stable
`canonical_sku` where available for SBERT + FAISS matching.
"""

import hashlib
import random
import re
from typing import Any

from app.models.schemas import ProductCreate
from app.services.ecommerce.base import EcommerceAdapter


def _seed_id(source: str, sku: str) -> str:
    return hashlib.sha256(f"{source}:{sku}".encode()).hexdigest()[:14]


def _query_matches(q: str | None, item: dict[str, Any]) -> bool:
    if not q or not q.strip():
        return True
    tokens = [t for t in re.split(r"\W+", q.lower()) if len(t) > 1]
    blob = " ".join(
        [
            " ".join(item.get("titles", {}).values()),
            item.get("description", ""),
            item.get("brand", ""),
            " ".join(item.get("keywords", [])),
        ]
    ).lower()
    return any(t in blob for t in tokens)


def _catalog_for_query(query: str | None, rng: random.Random, price_scale: float) -> list[dict[str, Any]]:
    base: list[dict[str, Any]] = [
        {
            "canonical_sku": "PHONE-IPH15-128-BLK",
            "brand": "Apple",
            "category": "phones",
            "keywords": ["iphone", "15", "128", "apple", "smartphone"],
            "description": "6.1-inch display, A16 chip, dual cameras, 5G.",
            "titles": {
                "amazon": "Apple iPhone 15 (128 GB) — Black",
                "flipkart": "iPhone 15 128GB Black 5G with A16 Bionic",
                "croma": "Apple iPhone 15 128 GB: Black | 1 Year Warranty",
                "meesho": "i phone 15 128gb black colour latest model 5g mobile",
            },
            "price_inr": 72999,
            "rating_amazon": 4.6,
            "rating_flipkart": 4.5,
            "rating_croma": 4.55,
            "rating_meesho": 4.1,
            "reviews": [
                "Excellent battery life and camera.",
                "Authentic box; fast delivery.",
                "Minor heating during gaming.",
                "Value for money during sale.",
            ],
            "offer_amazon": "10% instant discount with bank card",
            "offer_flipkart": "Exchange bonus up to ₹8000",
            "offer_croma": "₹2000 cashback + extended warranty",
            "offer_meesho": "Lowest price challenge + free delivery",
            "discount_pct_amazon": 8.0,
            "discount_pct_flipkart": 6.0,
            "discount_pct_croma": 5.0,
            "discount_pct_meesho": 12.0,
            "delivery_days": {"amazon": 2, "flipkart": 3, "croma": 2, "meesho": 5},
            "delivery_text": {
                "amazon": "Prime eligible — 1–2 days",
                "flipkart": "Express in metro — 2–3 days",
                "croma": "Store pickup / 2-day home",
                "meesho": "Standard courier — 4–6 days",
            },
            "free_shipping": {"amazon": True, "flipkart": True, "croma": True, "meesho": True},
            "review_count": {"amazon": 12400, "flipkart": 9800, "croma": 1200, "meesho": 3400},
        },
        {
            "canonical_sku": "HEAT-ROOM-2000W",
            "brand": "WarmAir",
            "category": "appliances",
            "keywords": ["heater", "room", "2000", "oil", "fan"],
            "description": "2000W room heater with thermostat and tip-over protection.",
            "titles": {
                "amazon": "WarmAir 2000W Oil Filled Radiator Room Heater (9 Fins)",
                "flipkart": "WarmAir OFR 9 Fin 2000 Watt Room Heater with ISI mark",
                "croma": "WarmAir 2000W Oil Radiator Heater — 9 fins, white",
                "meesho": "2000 watt oil heater 9 fin room warmer ISI",
            },
            "price_inr": 6499,
            "rating_amazon": 4.2,
            "rating_flipkart": 4.3,
            "rating_croma": 4.35,
            "rating_meesho": 3.9,
            "reviews": [
                "Heats a medium room well.",
                "Takes time to warm up.",
                "Good build; noisy fan mode.",
            ],
            "offer_amazon": "5% coupon on first appliance buy",
            "offer_flipkart": "No-cost EMI 6 months",
            "offer_croma": "Free installation in select cities",
            "offer_meesho": "Combo discount with extension cord",
            "discount_pct_amazon": 5.0,
            "discount_pct_flipkart": None,
            "discount_pct_croma": 7.0,
            "discount_pct_meesho": 10.0,
            "delivery_days": {"amazon": 3, "flipkart": 2, "croma": 1, "meesho": 6},
            "delivery_text": {
                "amazon": "3–4 days",
                "flipkart": "1-day in select pincodes",
                "croma": "Same-day pickup at store",
                "meesho": "5–7 days",
            },
            "free_shipping": {"amazon": True, "flipkart": True, "croma": False, "meesho": True},
            "review_count": {"amazon": 2100, "flipkart": 1800, "croma": 400, "meesho": 900},
        },
        {
            "canonical_sku": "HEADPHONE-ANC-TWS",
            "brand": "SoundWave",
            "category": "audio",
            "keywords": ["headphone", "earbuds", "wireless", "anc", "bluetooth", "tws"],
            "description": "Hybrid ANC TWS earbuds, IPX4, transparency mode.",
            "titles": {
                "amazon": "SoundWave Buds Pro ANC True Wireless Earbuds (White)",
                "flipkart": "SoundWave TWS ANC earbuds Pro white colour",
                "croma": "SoundWave Buds Pro — Active Noise Cancellation, White",
                "meesho": "wireless bluetooth anc earbuds pro white soundwave",
            },
            "price_inr": 8999,
            "rating_amazon": 4.4,
            "rating_flipkart": 4.35,
            "rating_croma": 4.5,
            "rating_meesho": 4.0,
            "reviews": [
                "ANC works great on flights.",
                "Mic is average for calls.",
                "Comfortable for long use.",
            ],
            "offer_amazon": "Bank offer ₹750 off",
            "offer_flipkart": "Buy with soundbar — extra 8% off",
            "offer_croma": "2-year damage protection plan",
            "offer_meesho": "First order ₹500 off",
            "discount_pct_amazon": 7.0,
            "discount_pct_flipkart": 9.0,
            "discount_pct_croma": 4.0,
            "discount_pct_meesho": 11.0,
            "delivery_days": {"amazon": 2, "flipkart": 2, "croma": 3, "meesho": 5},
            "delivery_text": {
                "amazon": "Prime 1–2 days",
                "flipkart": "2-day delivery",
                "croma": "3–5 days home",
                "meesho": "5–8 days",
            },
            "free_shipping": {"amazon": True, "flipkart": True, "croma": True, "meesho": True},
            "review_count": {"amazon": 5600, "flipkart": 4200, "croma": 900, "meesho": 2100},
        },
    ]

    if query and query.strip():
        base = [b for b in base if _query_matches(query, b)]
        if not base:
            q = query.strip()
            base = [
                {
                    "canonical_sku": None,
                    "brand": "Generic",
                    "category": "general",
                    "keywords": [q.lower()],
                    "description": f"Cross-platform search result for {q}.",
                    "titles": {
                        "amazon": f"{q} — Amazon India",
                        "flipkart": f"{q} | Flipkart",
                        "croma": f"{q} — Croma",
                        "meesho": f"{q} — Meesho",
                    },
                    "price_inr": int(rng.uniform(499, 24999)),
                    "rating_amazon": round(rng.uniform(3.8, 4.7), 2),
                    "rating_flipkart": round(rng.uniform(3.8, 4.7), 2),
                    "rating_croma": round(rng.uniform(3.8, 4.7), 2),
                    "rating_meesho": round(rng.uniform(3.5, 4.4), 2),
                    "reviews": [
                        "Product as described.",
                        rng.choice(["Good value.", "Average quality.", "Happy with purchase."]),
                    ],
                    "offer_amazon": "Coupon available",
                    "offer_flipkart": "SuperCoin offers",
                    "offer_croma": "Extended warranty optional",
                    "offer_meesho": "Lowest price zone",
                    "discount_pct_amazon": 5.0,
                    "discount_pct_flipkart": 6.0,
                    "discount_pct_croma": 4.0,
                    "discount_pct_meesho": 10.0,
                    "delivery_days": {"amazon": 3, "flipkart": 3, "croma": 2, "meesho": 6},
                    "delivery_text": {
                        "amazon": "Standard delivery",
                        "flipkart": "Standard delivery",
                        "croma": "2–4 days",
                        "meesho": "5–9 days",
                    },
                    "free_shipping": {"amazon": True, "flipkart": rng.choice([True, False]), "croma": True, "meesho": True},
                    "review_count": {
                        "amazon": rng.randint(50, 2000),
                        "flipkart": rng.randint(50, 2000),
                        "croma": rng.randint(20, 500),
                        "meesho": rng.randint(30, 1200),
                    },
                }
            ]

    out = []
    for b in base:
        row = dict(b)
        row["price_inr"] = int(round(float(row["price_inr"]) * price_scale * rng.uniform(0.96, 1.04)))
        sku = row.get("canonical_sku") or row["titles"]["amazon"][:24]
        row["image_url"] = f"https://picsum.photos/seed/{_seed_id('img', sku)}/400/300"
        out.append(row)
    return out


def _item_to_product_create(row: dict[str, Any], store: str) -> ProductCreate:
    cid = row.get("canonical_sku") or row["titles"][store]
    rating_key = f"rating_{store}"
    rating = float(row.get(rating_key, 4.2))
    rc = int(row["review_count"][store])
    return ProductCreate(
        source=store,
        external_id=_seed_id(store, str(cid)),
        title=row["titles"][store],
        description=row["description"],
        category=row["category"],
        brand=row.get("brand"),
        image_url=row.get("image_url"),
        price=float(row["price_inr"]),
        currency="INR",
        rating=rating,
        review_count=rc,
        reviews=list(row.get("reviews", []))[:20],
        canonical_sku=row.get("canonical_sku"),
        offer_label=row.get(f"offer_{store}"),
        discount_pct=row.get(f"discount_pct_{store}"),
        delivery_days=int(row["delivery_days"][store]),
        delivery_text=str(row["delivery_text"][store]),
        free_shipping=bool(row["free_shipping"][store]),
    )


def _make_adapter_class(store: str, price_bias: float):
    class Adapter(EcommerceAdapter):
        name = store

        async def fetch_products(self, query: str | None = None, limit: int = 50) -> list[ProductCreate]:
            rng = random.Random((query or "") + store + str(price_bias))
            rows = _catalog_for_query(query, rng, price_bias)
            return [_item_to_product_create(r, store) for r in rows[:limit]]

    Adapter.__name__ = f"{store.capitalize()}Adapter"
    return Adapter()


AmazonAdapter = _make_adapter_class("amazon", 1.0)
FlipkartAdapter = _make_adapter_class("flipkart", 0.98)
CromaAdapter = _make_adapter_class("croma", 1.02)
MeeshoAdapter = _make_adapter_class("meesho", 0.92)
