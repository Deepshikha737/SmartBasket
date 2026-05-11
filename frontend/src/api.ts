import axios from "axios";

const client = axios.create({
  baseURL: import.meta.env.VITE_API_URL || "",
  timeout: 180000,
});

export type Product = {
  id: string;
  title: string;
  description?: string;
  category: string;
  brand?: string | null;
  source: string;
  external_id: string;
  price: number;
  currency: string;
  rating?: number | null;
  review_count: number;
  offer_label?: string | null;
  discount_pct?: number | null;
  delivery_days?: number;
  delivery_text?: string;
  free_shipping?: boolean;
};

export type ScoreBreakdown = {
  price: number;
  rating: number;
  sentiment: number;
  offer: number;
  delivery: number;
  free_shipping_bonus: number;
  total: number;
};

export type ComparedListing = {
  product: Product;
  sentiment_positive_ratio: number;
  sentiment_negative_ratio: number;
  sentiment_review_count: number;
  trust_index: number;
  score_breakdown: ScoreBreakdown;
};

export type ProductGroupResult = {
  group_id: string;
  display_name: string;
  semantic_match_score?: number | null;
  listings: ComparedListing[];
  best_listing_product_id?: string | null;
  best_store?: string | null;
  recommendation_summary: string;
  best_price_store?: string | null;
  best_overall_store?: string | null;
  best_delivery_store?: string | null;
  best_price_rationale: string;
  best_overall_rationale: string;
  best_delivery_rationale: string;
};

export type StoreSentimentRollup = {
  store: string;
  positive_ratio: number;
  negative_ratio: number;
  reviews_analyzed: number;
  avg_rating: number;
  trust_score: number;
  summary: string;
};

export type UnifiedSearchResponse = {
  query: string;
  sources_queried: string[];
  groups: ProductGroupResult[];
  alternatives: Record<string, unknown>;
  sync_note: string;
  store_sentiment_rollups: StoreSentimentRollup[];
  final_ai_recommendation: string;
};

export async function unifiedSearch(q: string, limitPerVendor = 24) {
  const { data } = await client.get<UnifiedSearchResponse>("/api/search/unified", {
    params: { q, limit_per_vendor: limitPerVendor, rebuild_index: true },
  });
  return data;
}
