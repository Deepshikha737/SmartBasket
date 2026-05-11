"""
Derive per-group platform awards, store-level sentiment rollups, and session narrative.
"""

import math
from typing import Any, Optional

from app.models.schemas import ComparedListing, StoreSentimentRollup


def best_price_platform(listings: list[ComparedListing]) -> Optional[str]:
    if not listings:
        return None
    best = min(listings, key=lambda L: L.product.get("price", float("inf")))
    return str(best.product.get("source"))


def best_delivery_platform(listings: list[ComparedListing]) -> Optional[str]:
    if not listings:
        return None

    def sort_key(L: ComparedListing) -> tuple:
        p = L.product
        days = int(p.get("delivery_days") or 99)
        free = 0 if p.get("free_shipping") else 1
        rating = float(p.get("rating") or 0)
        return (days, free, -rating)

    best = min(listings, key=sort_key)
    return str(best.product.get("source"))


def best_overall_platform(listings: list[ComparedListing]) -> Optional[str]:
    if not listings:
        return None
    best = max(listings, key=lambda L: L.score_breakdown.total)
    return str(best.product.get("source"))


def _platform_label(store: str) -> str:
    names = {"amazon": "Amazon", "flipkart": "Flipkart", "croma": "Croma", "meesho": "Meesho"}
    return names.get(store.lower(), store.replace("_", " ").title())


def group_award_rationale(
    kind: str,
    store: str,
    listings: list[ComparedListing],
) -> str:
    if not store:
        return ""
    label = _platform_label(store)
    if kind == "price":
        p = next(L for L in listings if L.product.get("source") == store)
        return f"{label} lists the lowest price at ₹{p.product.get('price', 0):,.0f} for this match."
    if kind == "delivery":
        p = next(L for L in listings if L.product.get("source") == store)
        d = p.product.get("delivery_days", "?")
        fs = " with free delivery" if p.product.get("free_shipping") else ""
        return f"{label} offers the fastest stated delivery ({d} day(s)){fs} among compared listings."
    p = next(L for L in listings if L.product.get("source") == store)
    return (
        f"{label} leads on the composite score ({p.score_breakdown.total:.2f}) blending price, "
        f"ratings, sentiment, offers, and logistics."
    )


def listing_trust_index(pos_ratio: float, review_n: int, rating: Optional[float]) -> float:
    r = (rating or 0.0) / 5.0
    vol = min(1.0, math.log1p(max(1, review_n)) / math.log1p(400))
    return round(min(100, 100 * (0.45 * pos_ratio + 0.35 * r + 0.20 * vol)), 1)


def build_store_rollups(all_listings: list[ComparedListing]) -> list[StoreSentimentRollup]:
    from collections import defaultdict

    acc: dict[str, dict[str, Any]] = defaultdict(
        lambda: {"pos_w": 0.0, "neg_w": 0.0, "w": 0, "ratings": []}
    )
    for L in all_listings:
        s = str(L.product.get("source"))
        w = max(1, int(L.sentiment_review_count))
        acc[s]["pos_w"] += float(L.sentiment_positive_ratio) * w
        acc[s]["neg_w"] += float(L.sentiment_negative_ratio) * w
        acc[s]["w"] += w
        acc[s]["ratings"].append(float(L.product.get("rating") or 0.0))

    out: list[StoreSentimentRollup] = []
    for store in sorted(acc.keys()):
        v = acc[store]
        w = max(1, v["w"])
        pos = v["pos_w"] / w
        neg = v["neg_w"] / w
        avg_r = sum(v["ratings"]) / len(v["ratings"]) if v["ratings"] else 0.0
        trust = min(
            100.0,
            40 * pos + 35 * min(1.0, avg_r / 5.0) + 25 * min(1.0, math.log1p(w) / math.log1p(800)),
        )
        pl = _platform_label(store)
        summary = (
            f"{pl}: sentiment skews ~{(pos * 100):.0f}% positive / {(neg * 100):.0f}% negative "
            f"on analyzed snippets; aggregate rating {avg_r:.2f}/5; trust score {trust:.0f}/100."
        )
        out.append(
            StoreSentimentRollup(
                store=store,
                positive_ratio=round(pos, 4),
                negative_ratio=round(neg, 4),
                reviews_analyzed=int(w),
                avg_rating=round(avg_r, 2),
                trust_score=round(trust, 1),
                summary=summary,
            )
        )
    return out


def session_final_recommendation(
    groups: list[tuple[str, Optional[str], Optional[str], Optional[str]]],
) -> str:
    """
    groups: list of (display_name, best_overall, best_price, best_delivery)
    """
    if not groups:
        return "No comparable listings were found for this search. Try a broader product name."

    overall_wins: dict[str, int] = {}
    for _name, ov, _bp, _bd in groups:
        if ov:
            overall_wins[ov] = overall_wins.get(ov, 0) + 1

    if not overall_wins:
        top = groups[0]
        return (
            f"For “{top[0]}”, compare the table above and weigh price against delivery and review sentiment "
            "before you check out."
        )

    leader = max(overall_wins, key=lambda k: overall_wins[k])
    count = overall_wins[leader]
    leader_label = _platform_label(leader)
    return (
        f"Across {len(groups)} matched product cluster(s), {leader_label} wins best overall value "
        f"on {count} of them — prioritizing balanced price, ratings, offers, sentiment, and delivery. "
        f"Still compare best price and fastest delivery callouts per product when those matter more to you."
    )
