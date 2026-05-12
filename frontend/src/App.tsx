import { useState } from "react";
import {
  type ComparedListing,
  type ProductGroupResult,
  type StoreSentimentRollup,
  type UnifiedSearchResponse,
  unifiedSearch,
} from "./api";

const PLATFORM_NAMES: Record<string, string> = {
  amazon: "Amazon",
  flipkart: "Flipkart",
  croma: "Croma",
  meesho: "Meesho",
};

function platformName(source: string) {
  return PLATFORM_NAMES[source.toLowerCase()] ?? source.charAt(0).toUpperCase() + source.slice(1);
}

function fmtMoney(p: ComparedListing["product"]) {
  const cur = p.currency || "INR";
  const n = p.price;
  if (cur === "INR") return `₹${n.toLocaleString("en-IN", { maximumFractionDigits: 0 })}`;
  return `${cur} ${n.toFixed(2)}`;
}

function ComparisonTable({ group }: { group: ProductGroupResult }) {
  return (
    <div className="overflow-x-auto rounded-xl border border-slate-200 bg-white shadow-sm">
      <table className="w-full min-w-[720px] text-left text-sm">
        <thead>
          <tr className="border-b border-slate-100 bg-slate-50/80 text-xs font-semibold uppercase tracking-wide text-slate-500">
            <th className="px-4 py-3">Store</th>
            <th className="px-4 py-3">Product</th>
            <th className="px-4 py-3 text-right">Price</th>
            <th className="px-4 py-3 text-right">Rating</th>
            <th className="px-4 py-3">Delivery</th>
            <th className="px-4 py-3">Offers / cashback</th>
          </tr>
        </thead>
        <tbody>
          {group.listings.map((L) => {
            const p = L.product;
            const highlight = p.id === group.best_listing_product_id;
            return (
              <tr
                key={p.id}
                className={`border-b border-slate-100 last:border-0 ${
                  highlight ? "bg-emerald-50/90" : "hover:bg-slate-50/80"
                }`}
              >
                <td className="px-4 py-3 font-semibold text-slate-800">{platformName(p.source)}</td>
                <td className="max-w-xs px-4 py-3 text-slate-700">
                  <div className="line-clamp-2" title={p.title}>
                    {p.title}
                  </div>
                </td>
                <td className="px-4 py-3 text-right font-mono text-sm font-semibold text-emerald-700">
                  {fmtMoney(p)}
                </td>
                <td className="px-4 py-3 text-right text-amber-700">{p.rating ?? "—"}</td>
                <td className="px-4 py-3 text-slate-600">
                  <span className="font-medium text-slate-800">{p.delivery_days ?? "—"} days</span>
                  {p.free_shipping ? (
                    <span className="ml-1 text-xs font-medium text-emerald-600">· Free delivery</span>
                  ) : null}
                  <div className="max-w-[220px] truncate text-xs text-slate-500">{p.delivery_text}</div>
                </td>
                <td className="px-4 py-3 text-slate-600">
                  {p.offer_label ?? "—"}
                  {p.discount_pct != null ? (
                    <span className="ml-1 text-xs font-medium text-emerald-700">({p.discount_pct}% off)</span>
                  ) : null}
                </td>
              </tr>
            );
          })}
        </tbody>
      </table>
    </div>
  );
}

function InsightCards({ group }: { group: ProductGroupResult }) {
  const cards = [
    {
      title: "Best price",
      store: group.best_price_store,
      body: group.best_price_rationale,
      ring: "ring-orange-100",
      accent: "text-orange-700",
    },
    {
      title: "Best overall value",
      store: group.best_overall_store,
      body: group.best_overall_rationale,
      ring: "ring-emerald-100",
      accent: "text-emerald-700",
    },
    {
      title: "Fastest delivery",
      store: group.best_delivery_store,
      body: group.best_delivery_rationale,
      ring: "ring-violet-100",
      accent: "text-violet-700",
    },
  ];
  return (
    <div className="mt-4 grid gap-4 sm:grid-cols-3">
      {cards.map((c) => (
        <div
          key={c.title}
          className={`rounded-2xl border border-slate-200 bg-white p-5 shadow-sm ring-1 ${c.ring}`}
        >
          <p className="text-xs font-semibold uppercase tracking-wide text-slate-500">{c.title}</p>
          <p className={`mt-2 font-display text-xl font-bold ${c.accent}`}>
            {c.store ? platformName(c.store) : "—"}
          </p>
          <p className="mt-2 text-sm leading-relaxed text-slate-600">{c.body || "—"}</p>
        </div>
      ))}
    </div>
  );
}

function SentimentPerListing({ group }: { group: ProductGroupResult }) {
  return (
    <div className="mt-4 grid gap-3 sm:grid-cols-2">
      {group.listings.map((L) => {
        const p = L.product;
        const pos = Math.round(L.sentiment_positive_ratio * 100);
        const neg = Math.round(L.sentiment_negative_ratio * 100);
        return (
          <div
            key={p.id}
            className="rounded-xl border border-slate-200 bg-white px-4 py-3 shadow-sm"
          >
            <p className="text-sm font-semibold text-slate-800">{platformName(p.source)}</p>
            <p className="mt-1 text-sm text-slate-600">
              <span className="text-emerald-700">{pos}%</span> positive ·{" "}
              <span className="text-rose-600">{neg}%</span> negative
            </p>
            <p className="mt-1 text-xs text-slate-500">
              Trust index <span className="font-semibold text-slate-800">{L.trust_index}</span> / 100 · DistilBERT
              on {L.sentiment_review_count} review snippet(s)
            </p>
          </div>
        );
      })}
    </div>
  );
}

function StoreRollups({ rows }: { rows: StoreSentimentRollup[] }) {
  if (!rows.length) return null;
  return (
    <div className="mt-4 grid gap-4 sm:grid-cols-2 lg:grid-cols-4">
      {rows.map((r) => (
        <div key={r.store} className="rounded-2xl border border-slate-200 bg-white p-4 shadow-sm">
          <p className="text-sm font-semibold text-slate-800">{platformName(r.store)}</p>
          <p className="mt-2 text-3xl font-bold text-sky-600">{r.trust_score}</p>
          <p className="text-xs font-medium uppercase tracking-wide text-slate-500">Trust score</p>
          <p className="mt-2 text-xs leading-relaxed text-slate-600">{r.summary}</p>
        </div>
      ))}
    </div>
  );
}

type RecItem = {
  title?: string;
  price?: number;
  similarity?: number;
  source?: string;
  brand?: string | null;
};

function RecommendationCard({ item }: { item: RecItem }) {
  return (
    <article className="flex min-w-[260px] max-w-sm flex-shrink-0 flex-col rounded-2xl border border-slate-200 bg-white p-4 shadow-sm transition hover:shadow-md">
      <p className="line-clamp-2 text-sm font-medium leading-snug text-slate-800">{item.title}</p>
      {item.brand ? <p className="mt-1 text-xs text-slate-500">{item.brand}</p> : null}
      <p className="mt-3 font-mono text-lg font-semibold text-emerald-700">
        {item.price != null ? `₹${item.price.toLocaleString("en-IN")}` : ""}
      </p>
      <div className="mt-2 flex flex-wrap items-center gap-2 text-xs text-slate-500">
        {item.source ? (
          <span className="rounded-full bg-slate-100 px-2 py-0.5 font-medium text-slate-700">
            {platformName(item.source)}
          </span>
        ) : null}
        {item.similarity != null ? (
          <span className="text-slate-400">Match {item.similarity.toFixed(2)}</span>
        ) : null}
      </div>
    </article>
  );
}

function RecommendationRow({ title, subtitle, items }: { title: string; subtitle?: string; items: RecItem[] }) {
  if (!items?.length) return null;
  return (
    <div className="mt-8">
      <h4 className="text-sm font-semibold text-slate-800">{title}</h4>
      {subtitle ? <p className="mt-0.5 text-xs text-slate-500">{subtitle}</p> : null}
      <div className="mt-3 flex gap-3 overflow-x-auto pb-2 pt-1 [-ms-overflow-style:none] [scrollbar-width:thin]">
        {items.slice(0, 8).map((item, i) => (
          <RecommendationCard key={`${title}-${i}`} item={item} />
        ))}
      </div>
    </div>
  );
}

function AlternativesSection({ data }: { data: UnifiedSearchResponse["alternatives"] }) {
  if (!data || typeof data !== "object" || "error" in data) return null;
  const sim = (data.similar as RecItem[]) || [];
  const cheap = (data.cheaper as RecItem[]) || [];
  const prem = (data.premium as RecItem[]) || [];
  const models = (data.similar_models as RecItem[]) || [];
  if (!sim.length && !cheap.length && !prem.length && !models.length) return null;
  return (
    <section className="mt-12 rounded-2xl border border-slate-200 bg-white p-6 shadow-sm">
      <h2 className="font-display text-lg font-bold text-slate-900">You may also like</h2>
      <p className="mt-1 text-sm text-slate-500">
        Semantic recommendations (SBERT + FAISS). Not part of the price comparison above.
      </p>
      <RecommendationRow
        title="Similar products"
        subtitle="Closest embeddings to your top match"
        items={sim}
      />
      <RecommendationRow
        title="Similar models & other brands"
        subtitle="Same category, different brand — discovery picks"
        items={models}
      />
      <RecommendationRow title="Cheaper alternatives" items={cheap} />
      <RecommendationRow title="Premium alternatives" items={prem} />
    </section>
  );
}

export default function App() {
  const [q, setQ] = useState("iPhone 15");
  const [busy, setBusy] = useState(false);
  const [err, setErr] = useState<string | null>(null);
  const [res, setRes] = useState<UnifiedSearchResponse | null>(null);

  const onSearch = async () => {
    const query = q.trim();
    if (!query) return;
    setBusy(true);
    setErr(null);
    setRes(null);
    try {
      setRes(await unifiedSearch(query));
    } catch {
      setErr("Could not reach the API. Start the backend and MongoDB, then try again.");
      setRes(null);
    } finally {
      setBusy(false);
    }
  };

  return (
    <div className="min-h-screen">
      <header className="border-b border-slate-200 bg-white shadow-sm">
        <div className="mx-auto flex max-w-5xl flex-col items-center gap-2 px-4 py-10 text-center sm:py-12">
          <p className="text-xs font-semibold uppercase tracking-[0.2em] text-orange-600">Price compare</p>
          <h1 className="font-display text-3xl font-bold tracking-tight text-slate-900 sm:text-4xl">
            Find the best deal across stores
          </h1>
          <p className="max-w-2xl text-sm leading-relaxed text-slate-600">
            Search once on <strong className="font-semibold text-slate-800">Amazon</strong>,{" "}
            <strong className="font-semibold text-slate-800">Flipkart</strong>,{" "}
            <strong className="font-semibold text-slate-800">Croma</strong>, and{" "}
            <strong className="font-semibold text-slate-800">Meesho</strong>. We align listings with different titles
            using SBERT + FAISS, compare price, delivery, and offers, run DistilBERT sentiment on reviews, and
            suggest where to buy.
          </p>
        </div>
      </header>

      <main className="mx-auto max-w-5xl px-4 py-8 sm:py-10">
        <div className="mx-auto flex max-w-2xl flex-col gap-3 sm:flex-row">
          <input
            type="search"
            value={q}
            onChange={(e) => setQ(e.target.value)}
            onKeyDown={(e) => e.key === "Enter" && void onSearch()}
            placeholder="Search e.g. iPhone 15, heater, headphones…"
            className="flex-1 rounded-xl border border-slate-300 bg-white px-4 py-3 text-sm text-slate-900 shadow-sm placeholder:text-slate-400 focus:border-orange-400 focus:outline-none focus:ring-2 focus:ring-orange-200"
          />
          <button
            type="button"
            disabled={busy}
            onClick={() => void onSearch()}
            className="rounded-xl bg-orange-500 px-8 py-3 text-sm font-semibold text-white shadow-md transition hover:bg-orange-600 disabled:opacity-50"
          >
            {busy ? "Searching…" : "Search stores"}
          </button>
        </div>

        {err ? <p className="mx-auto mt-6 max-w-xl text-center text-sm text-rose-600">{err}</p> : null}

        {res ? (
          <div className="mt-10 space-y-10">
            {res.groups.map((group) => (
              <section key={group.group_id} className="rounded-2xl border border-slate-200 bg-white p-6 shadow-sm">
                <h2 className="font-display text-lg font-bold text-slate-900">{group.display_name}</h2>

                <h3 className="mt-6 text-xs font-bold uppercase tracking-wide text-slate-500">Price comparison</h3>
                <ComparisonTable group={group} />

                <h3 className="mt-8 text-xs font-bold uppercase tracking-wide text-slate-500">
                  AI purchase recommendation
                </h3>
                <InsightCards group={group} />
                <div className="mt-4 rounded-xl border border-emerald-100 bg-emerald-50/50 p-4">
                  <p className="text-sm leading-relaxed text-slate-800">
                    <span className="font-semibold text-emerald-800">Summary: </span>
                    {group.recommendation_summary}
                  </p>
                </div>

                <h3 className="mt-8 text-xs font-bold uppercase tracking-wide text-slate-500">
                  Review sentiment (DistilBERT)
                </h3>
                <SentimentPerListing group={group} />
              </section>
            ))}

            {res.store_sentiment_rollups?.length ? (
              <section className="rounded-2xl border border-slate-200 bg-white p-6 shadow-sm">
                <h2 className="font-display text-lg font-bold text-slate-900">Platform trust overview</h2>
                <p className="mt-1 text-sm text-slate-600">
                  Reliability signal from aggregated review sentiment and ratings for this search.
                </p>
                <StoreRollups rows={res.store_sentiment_rollups} />
              </section>
            ) : null}

            {res.final_ai_recommendation ? (
              <section className="rounded-2xl border border-sky-200 bg-sky-50/80 p-6 text-center shadow-sm">
                <h2 className="text-xs font-bold uppercase tracking-wide text-sky-800">Final recommendation</h2>
                <p className="mx-auto mt-3 max-w-3xl text-sm leading-relaxed text-slate-800">
                  {res.final_ai_recommendation}
                </p>
              </section>
            ) : null}

            <AlternativesSection data={res.alternatives} />
          </div>
        ) : null}
      </main>

      <footer className="mt-auto border-t border-slate-200 bg-white py-6 text-center text-xs text-slate-500">
        PCS — Amazon · Flipkart · Croma · Meesho · SBERT · FAISS · DistilBERT
      </footer>
    </div>
  );
}
