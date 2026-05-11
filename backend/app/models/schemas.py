from datetime import datetime
from typing import Any, Literal, Optional

from pydantic import BaseModel, Field


class ProductBase(BaseModel):
    title: str
    description: str = ""
    category: str = "general"
    brand: Optional[str] = None
    image_url: Optional[str] = None
    offer_label: Optional[str] = None
    discount_pct: Optional[float] = None
    delivery_days: int = 5
    delivery_text: str = ""
    free_shipping: bool = False


class ProductCreate(ProductBase):
    source: str
    external_id: str
    price: float
    currency: str = "USD"
    rating: Optional[float] = None
    review_count: int = 0
    reviews: list[str] = Field(default_factory=list)
    canonical_sku: Optional[str] = None


class ProductOut(ProductBase):
    id: str = Field(alias="_id")
    source: str
    external_id: str
    price: float
    currency: str
    rating: Optional[float] = None
    review_count: int = 0
    reviews_sample: list[str] = Field(default_factory=list)
    matched_group_id: Optional[str] = None
    updated_at: Optional[datetime] = None

    model_config = {"populate_by_name": True, "from_attributes": True}


class CompareRequest(BaseModel):
    product_ids: list[str] = Field(..., min_length=2, max_length=12)


class SemanticSearchRequest(BaseModel):
    query: str = Field(..., min_length=1, max_length=512)
    top_k: int = Field(10, ge=1, le=50)


class UserPreferences(BaseModel):
    user_id: str
    max_price: Optional[float] = None
    preferred_categories: list[str] = Field(default_factory=list)
    min_rating: Optional[float] = None


class RecommendationRequest(BaseModel):
    product_id: str
    user_id: Optional[str] = None
    top_k: int = Field(8, ge=1, le=30)


class SentimentRequest(BaseModel):
    texts: Optional[list[str]] = None
    product_id: Optional[str] = None


class SentimentResult(BaseModel):
    label: str
    score: float
    text_preview: str


class PriceAlertCreate(BaseModel):
    user_id: str
    product_id: str
    target_price: float
    direction: Literal["below", "any_drop"] = "below"


class PriceAlertOut(BaseModel):
    id: str = Field(alias="_id")
    user_id: str
    product_id: str
    target_price: float
    direction: str
    active: bool
    created_at: datetime

    model_config = {"populate_by_name": True}


class SyncResponse(BaseModel):
    inserted: int
    updated: int
    sources: list[str]
    message: str


class RebuildIndexResponse(BaseModel):
    vectors: int
    dimension: int
    message: str


class PredictionOut(BaseModel):
    product_id: str
    predicted_next_price: float
    lstm_price: float
    xgboost_price: Optional[float] = None
    confidence_note: str
    model: str


class ListingScoreBreakdown(BaseModel):
    price: float
    rating: float
    sentiment: float
    offer: float
    delivery: float
    free_shipping_bonus: float
    total: float


class ComparedListing(BaseModel):
    product: dict[str, Any]
    sentiment_positive_ratio: float
    sentiment_negative_ratio: float
    sentiment_review_count: int
    trust_index: float = Field(..., description="0–100 blended trust from sentiment + rating + review volume")
    score_breakdown: ListingScoreBreakdown
    price_prediction_lstm: Optional[float] = None
    price_prediction_xgb: Optional[float] = None


class ProductGroupResult(BaseModel):
    group_id: str
    display_name: str
    semantic_match_score: Optional[float] = None
    listings: list[ComparedListing]
    best_listing_product_id: Optional[str] = None
    best_store: Optional[str] = None
    recommendation_summary: str
    best_price_store: Optional[str] = None
    best_overall_store: Optional[str] = None
    best_delivery_store: Optional[str] = None
    best_price_rationale: str = ""
    best_overall_rationale: str = ""
    best_delivery_rationale: str = ""


class StoreSentimentRollup(BaseModel):
    store: str
    positive_ratio: float
    negative_ratio: float
    reviews_analyzed: int
    avg_rating: float
    trust_score: float
    summary: str


class UnifiedSearchResponse(BaseModel):
    query: str
    sources_queried: list[str]
    groups: list[ProductGroupResult]
    alternatives: dict[str, Any] = Field(default_factory=dict)
    sync_note: str
    store_sentiment_rollups: list[StoreSentimentRollup] = Field(default_factory=list)
    final_ai_recommendation: str = ""
