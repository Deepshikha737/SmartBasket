from abc import ABC, abstractmethod
from typing import Any

from app.models.schemas import ProductCreate


class EcommerceAdapter(ABC):
    name: str

    @abstractmethod
    async def fetch_products(self, query: str | None = None, limit: int = 50) -> list[ProductCreate]:
        """Return normalized products from the vendor."""

    def _normalize(self, raw: dict[str, Any], source: str) -> ProductCreate:
        return ProductCreate(
            source=source,
            external_id=str(raw["id"]),
            title=raw["title"],
            description=raw.get("description", ""),
            category=raw.get("category", "general"),
            brand=raw.get("brand"),
            image_url=raw.get("image_url"),
            price=float(raw["price"]),
            currency=raw.get("currency", "USD"),
            rating=raw.get("rating"),
            review_count=int(raw.get("review_count", 0)),
            reviews=list(raw.get("reviews", []))[:20],
            canonical_sku=raw.get("canonical_sku"),
            offer_label=raw.get("offer_label"),
            discount_pct=raw.get("discount_pct"),
            delivery_days=int(raw.get("delivery_days", 5)),
            delivery_text=str(raw.get("delivery_text", "")),
            free_shipping=bool(raw.get("free_shipping", False)),
        )
