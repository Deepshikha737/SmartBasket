"""
Composite score to recommend a store listing within a matched product group.

Weights are tunable; defaults favor price, then rating + sentiment, then logistics/offers.
"""

from dataclasses import dataclass
from typing import Any, Optional

from app.models.schemas import ListingScoreBreakdown, ProductOut


@dataclass
class Weights:
    price: float = 0.28
    rating: float = 0.22
    sentiment: float = 0.22
    offer: float = 0.12
    delivery: float = 0.11
    free_ship: float = 0.05


def _norm_price_inverse(prices: list[float], p: float) -> float:
    lo, hi = min(prices), max(prices)
    if hi <= lo:
        return 1.0
    inv = (hi - p) / (hi - lo)
    return max(0.0, min(1.0, inv))


def _delivery_score(days: int) -> float:
    return max(0.0, 1.0 - min(1.0, days / 14.0))


def _offer_score(discount_pct: Optional[float], offer_label: Optional[str]) -> float:
    if discount_pct is not None and discount_pct > 0:
        return max(0.0, min(1.0, discount_pct / 35.0))
    if offer_label:
        ol = offer_label.lower()
        if "off" in ol or "%" in ol or "cashback" in ol or "bundle" in ol:
            return 0.55
        return 0.25
    return 0.0


def score_listing(
    product: ProductOut,
    sentiment_positive_ratio: float,
    prices_in_group: list[float],
    w: Optional[Weights] = None,
) -> ListingScoreBreakdown:
    w = w or Weights()
    rating = (product.rating or 0.0) / 5.0
    rating = max(0.0, min(1.0, rating))
    sent = max(0.0, min(1.0, sentiment_positive_ratio))
    pr = _norm_price_inverse(prices_in_group, product.price)
    off = _offer_score(product.discount_pct, product.offer_label)
    dlv = _delivery_score(product.delivery_days)
    fs = 1.0 if product.free_shipping else 0.0
    fs_bonus = w.free_ship * fs
    total = (
        w.price * pr
        + w.rating * rating
        + w.sentiment * sent
        + w.offer * off
        + w.delivery * dlv
        + fs_bonus
    )
    return ListingScoreBreakdown(
        price=round(pr, 4),
        rating=round(rating, 4),
        sentiment=round(sent, 4),
        offer=round(off, 4),
        delivery=round(dlv, 4),
        free_shipping_bonus=round(fs_bonus, 4),
        total=round(total, 4),
    )


def pick_best(rows: list[tuple[ProductOut, ListingScoreBreakdown]]) -> Optional[tuple[str, str]]:
    if not rows:
        return None
    best = max(rows, key=lambda x: x[1].total)
    return best[0].id, best[0].source


def build_recommendation_sentence(
    best: ProductOut,
    others: list[ProductOut],
    breakdown: ListingScoreBreakdown,
) -> str:
    if not others:
        return f"Only {best.source} has this match; score {breakdown.total:.2f} based on listing quality."
    cheaper = [o for o in others if o.price < best.price * 0.98]
    parts = [
        f"{best.source} is the best pick (composite {breakdown.total:.2f}) balancing price, reviews, sentiment, offers, and delivery.",
    ]
    if cheaper:
        parts.append(f"Lower headline prices exist on {', '.join({c.source for c in cheaper})} — check fees, delivery, and sentiment before switching.")
    return " ".join(parts)
