"""Only these retailer `source` values are indexed, compared, and recommended."""

from typing import Final

ALLOWED_PRODUCT_SOURCES: Final[frozenset[str]] = frozenset({"amazon", "flipkart", "croma", "meesho"})


def is_allowed_source(source: str | None) -> bool:
    if not source:
        return False
    return str(source).strip().lower() in ALLOWED_PRODUCT_SOURCES
