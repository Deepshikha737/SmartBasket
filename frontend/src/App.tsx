import { useEffect, useState } from "react";
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

const POPULAR_CHIPS = [
  "iPhone 15",
  "Wireless earbuds",
  "Room heater",
  "Smart TV 55\"",
  "Laptop under 50000",
  "Air fryer",
];

const RETAILERS = [
  { id: "amazon", name: "Amazon", bg: "from-amber-400 to-orange-500", text: "text-white" },
  { id: "flipkart", name: "Flipkart", bg: "from-blue-500 to-indigo-600", text: "text-white" },
  { id: "croma", name: "Croma", bg: "from-emerald-500 to-teal-600", text: "text-white" },
  { id: "meesho", name: "Meesho", bg: "from-fuchsia-500 to-rose-500", text: "text-white" },
];

function platformName(source: string) {
  return PLATFORM_NAMES[source.toLowerCase()] ?? source.charAt(0).toUpperCase() + source.slice(1);
}

function fmtMoney(p: ComparedListing["product"]) {
  const cur = p.currency || "INR";
  const n = p.price;
  if (cur === "INR") return `₹${n.toLocaleString("en-IN", { maximumFractionDigits: 0 })}`;
  return `${cur} ${n.toFixed(2)}`;
}

function IconSearch({ className }: { className?: string }) {
  return (
    <svg className={className} viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2">
      <circle cx="11" cy="11" r="7" />
      <path d="M21 21l-4.35-4.35" strokeLinecap="round" />
    </svg>
  );
}

function IconSparkles({ className }: { className?: string }) {
  return (
    <svg className={className} viewBox="0 0 24 24" fill="currentColor">
      <path d="M12 2l1.2 4.2L17 7l-3.8 1.8L12 13l-1.2-3.2L7 7l3.8-1.8L12 2zm7 9l.7 2.5 2.5.7-2.5.7-.7 2.5-.7-2.5-2.5-.7 2.5-.7L19 11zM5 15l.9 3.1L9 19l-3.1.9L5 23l-.9-3.1L1 19l3.1-.9L5 15z" />
    </svg>
  );
}

function SmartBasketLogo({ className = "h-9 w-9" }: { className?: string }) {
  return (
    <svg className={className} viewBox="0 0 40 40" fill="none" xmlns="http://www.w3.org/2000/svg">
      <defs>
        <linearGradient id="sb-grad" x1="8" y1="4" x2="32" y2="36" gradientUnits="userSpaceOnUse">
          <stop stopColor="#10b981" />
          <stop offset="0.5" stopColor="#14b8a6" />
          <stop offset="1" stopColor="#6366f1" />
        </linearGradient>
      </defs>
      <rect x="4" y="4" width="32" height="32" rx="10" fill="url(#sb-grad)" opacity="0.15" />
      <path
        d="M12 14h16l-1.5 12H13.5L12 14z"
        stroke="url(#sb-grad)"
        strokeWidth="2"
        strokeLinejoin="round"
        fill="none"
      />
      <path d="M14 14V12a6 6 0 0112 0v2" stroke="url(#sb-grad)" strokeWidth="2" strokeLinecap="round" />
      <circle cx="28" cy="10" r="3" fill="#6366f1" opacity="0.9" />
      <path d="M27 10h2M28 9v2" stroke="white" strokeWidth="0.8" strokeLinecap="round" />
    </svg>
  );
}

function HeroIllustration() {
  return (
    <div className="relative mx-auto mt-8 max-w-lg lg:mt-0 lg:max-w-none">
      <div className="absolute -right-4 -top-6 h-24 w-24 rounded-full bg-gradient-to-br from-violet-400/30 to-fuchsia-400/20 blur-2xl animate-float" />
      <div className="absolute -bottom-4 -left-8 h-32 w-32 rounded-full bg-gradient-to-tr from-emerald-400/25 to-cyan-400/20 blur-2xl animate-float-delayed" />
      <svg viewBox="0 0 400 320" className="relative w-full drop-shadow-2xl" xmlns="http://www.w3.org/2000/svg">
        <defs>
          <linearGradient id="g1" x1="0%" y1="0%" x2="100%" y2="100%">
            <stop offset="0%" stopColor="#10b981" stopOpacity="0.35" />
            <stop offset="100%" stopColor="#6366f1" stopOpacity="0.45" />
          </linearGradient>
          <linearGradient id="g2" x1="0%" y1="100%" x2="100%" y2="0%">
            <stop offset="0%" stopColor="#f59e0b" stopOpacity="0.25" />
            <stop offset="100%" stopColor="#ec4899" stopOpacity="0.2" />
          </linearGradient>
        </defs>
        <rect x="40" y="48" width="320" height="200" rx="24" fill="white" stroke="url(#g1)" strokeWidth="2" />
        <rect x="60" y="72" width="120" height="72" rx="12" fill="url(#g2)" />
        <circle cx="96" cy="108" r="18" fill="#fff" opacity="0.9" />
        <rect x="200" y="80" width="140" height="10" rx="5" fill="#e2e8f0" />
        <rect x="200" y="100" width="100" height="8" rx="4" fill="#f1f5f9" />
        <rect x="200" y="118" width="80" height="8" rx="4" fill="#f1f5f9" />
        <g stroke="#6366f1" strokeWidth="1.5" fill="none" opacity="0.7">
          <path d="M280 200 L320 140 L360 200" />
          <circle cx="320" cy="130" r="8" fill="#6366f1" fillOpacity="0.3" />
          <circle cx="280" cy="200" r="6" fill="#10b981" fillOpacity="0.4" />
          <circle cx="360" cy="200" r="6" fill="#10b981" fillOpacity="0.4" />
        </g>
        <rect x="70" y="180" width="260" height="44" rx="12" fill="#f8fafc" stroke="#e2e8f0" />
        <rect x="86" y="194" width="72" height="16" rx="8" fill="#10b981" opacity="0.85" />
        <text x="200" y="212" fontSize="11" fill="#64748b" fontFamily="system-ui">
          AI matched · best store highlighted
        </text>
      </svg>
    </div>
  );
}

function ComparisonTable({ group }: { group: ProductGroupResult }) {
  return (
    <div className="overflow-x-auto rounded-xl border border-slate-200/80 bg-white/90 shadow-lg shadow-slate-900/5 backdrop-blur">
      <table className="w-full min-w-[720px] text-left text-sm">
        <thead>
          <tr className="border-b border-slate-100 bg-gradient-to-r from-slate-50 to-white text-xs font-semibold uppercase tracking-wide text-slate-500">
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
                className={`border-b border-slate-100/80 last:border-0 transition ${
                  highlight ? "bg-emerald-50/95" : "hover:bg-slate-50/90"
                }`}
              >
                <td className="px-4 py-3 font-semibold text-slate-800">{platformName(p.source)}</td>
                <td className="max-w-xs px-4 py-3 text-slate-700">
                  <div className="line-clamp-2" title={p.title}>
                    {p.title}
                  </div>
                </td>
                <td className="px-4 py-3 text-right font-mono text-sm font-semibold text-emerald-700">{fmtMoney(p)}</td>
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
    { title: "Best price", store: group.best_price_store, body: group.best_price_rationale, grad: "from-orange-500 to-amber-500", bg: "from-orange-50 to-amber-50/80" },
    { title: "Best overall value", store: group.best_overall_store, body: group.best_overall_rationale, grad: "from-emerald-500 to-teal-500", bg: "from-emerald-50 to-teal-50/80" },
    { title: "Fastest delivery", store: group.best_delivery_store, body: group.best_delivery_rationale, grad: "from-violet-500 to-indigo-500", bg: "from-violet-50 to-indigo-50/80" },
  ];
  return (
    <div className="mt-4 grid gap-4 sm:grid-cols-3">
      {cards.map((c) => (
        <div
          key={c.title}
          className={`group rounded-2xl border border-white/80 bg-gradient-to-br ${c.bg} p-5 shadow-lg shadow-slate-900/5 transition hover:-translate-y-0.5 hover:shadow-xl`}
        >
          <p className="text-xs font-semibold uppercase tracking-wide text-slate-500">{c.title}</p>
          <p className={`mt-2 bg-gradient-to-r ${c.grad} bg-clip-text font-display text-xl font-bold text-transparent`}>
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
            className="rounded-xl border border-slate-200/80 bg-white/90 px-4 py-3 shadow-md backdrop-blur transition hover:shadow-lg"
          >
            <p className="text-sm font-semibold text-slate-800">{platformName(p.source)}</p>
            <p className="mt-1 text-sm text-slate-600">
              <span className="text-emerald-700">{pos}%</span> positive · <span className="text-rose-600">{neg}%</span>{" "}
              negative
            </p>
            <p className="mt-1 text-xs text-slate-500">
              Trust <span className="font-semibold text-slate-800">{L.trust_index}</span>/100 · DistilBERT ·{" "}
              {L.sentiment_review_count} snippets
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
        <div
          key={r.store}
          className="rounded-2xl border border-slate-200/80 bg-white/90 p-4 shadow-md backdrop-blur transition hover:-translate-y-0.5 hover:shadow-lg"
        >
          <p className="text-sm font-semibold text-slate-800">{platformName(r.store)}</p>
          <p className="mt-2 text-3xl font-bold text-sky-600">{r.trust_score}</p>
          <p className="text-xs font-medium uppercase tracking-wide text-slate-500">Trust score</p>
          <p className="mt-2 text-xs leading-relaxed text-slate-600">{r.summary}</p>
        </div>
      ))}
    </div>
  );
}

type RecItem = { title?: string; price?: number; similarity?: number; source?: string; brand?: string | null };

function RecommendationCard({ item }: { item: RecItem }) {
  return (
    <article className="flex min-w-[260px] max-w-sm flex-shrink-0 flex-col rounded-2xl border border-white/70 bg-white/80 p-4 shadow-lg backdrop-blur transition hover:-translate-y-1 hover:shadow-xl">
      <p className="line-clamp-2 text-sm font-medium leading-snug text-slate-800">{item.title}</p>
      {item.brand ? <p className="mt-1 text-xs text-slate-500">{item.brand}</p> : null}
      <p className="mt-3 font-mono text-lg font-semibold text-emerald-700">
        {item.price != null ? `₹${item.price.toLocaleString("en-IN")}` : ""}
      </p>
      <div className="mt-2 flex flex-wrap items-center gap-2 text-xs text-slate-500">
        {item.source ? (
          <span className="rounded-full bg-slate-100/90 px-2 py-0.5 font-medium text-slate-700">
            {platformName(item.source)}
          </span>
        ) : null}
        {item.similarity != null ? <span className="text-slate-400">Match {item.similarity.toFixed(2)}</span> : null}
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
      <div className="mt-3 flex gap-3 overflow-x-auto pb-2 pt-1 [scrollbar-width:thin]">
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
    <section className="glass-strong mt-12 rounded-3xl p-6 sm:p-8">
      <h2 className="font-display text-lg font-bold text-slate-900">You may also like</h2>
      <p className="mt-1 text-sm text-slate-600">Semantic picks powered by SBERT + FAISS — separate from the live comparison above.</p>
      <RecommendationRow title="Similar products" subtitle="Closest embeddings to your top match" items={sim} />
      <RecommendationRow title="Similar models & other brands" subtitle="Same category, different brand" items={models} />
      <RecommendationRow title="Cheaper alternatives" items={cheap} />
      <RecommendationRow title="Premium alternatives" items={prem} />
    </section>
  );
}

function FeatureCards() {
  const items = [
    { title: "AI price comparison", desc: "SBERT + FAISS align the same product across different titles and stores.", icon: "⚖️" },
    { title: "Smart recommendations", desc: "Similar, cheaper, and premium picks ranked by semantic similarity.", icon: "✨" },
    { title: "Sentiment analysis", desc: "DistilBERT reads review tone to surface trust signals per platform.", icon: "💬" },
    { title: "Similar product suggestions", desc: "Explore alternatives and other brands without leaving your flow.", icon: "🔗" },
  ];
  return (
    <section id="features" className="scroll-mt-24 mx-auto max-w-6xl px-4 py-14 sm:py-20">
      <h2 className="text-center font-display text-2xl font-bold text-slate-900 sm:text-3xl">Why teams choose SmartBasket</h2>
      <p className="mx-auto mt-2 max-w-2xl text-center text-sm text-slate-600 sm:text-base">
        Production-style pipelines for embeddings, vector search, and NLP — packaged for ecommerce discovery.
      </p>
      <div className="mt-10 grid gap-5 sm:grid-cols-2 lg:grid-cols-4">
        {items.map((f) => (
          <div
            key={f.title}
            className="group rounded-2xl border border-white/60 bg-white/45 p-6 shadow-xl shadow-indigo-950/5 backdrop-blur-xl transition hover:-translate-y-1 hover:border-emerald-200/80 hover:shadow-2xl"
          >
            <span className="text-3xl">{f.icon}</span>
            <h3 className="mt-4 font-display text-lg font-semibold text-slate-900">{f.title}</h3>
            <p className="mt-2 text-sm leading-relaxed text-slate-600">{f.desc}</p>
          </div>
        ))}
      </div>
    </section>
  );
}

function RetailerStrip() {
  return (
    <div className="mx-auto max-w-4xl px-4">
      <p className="text-center text-xs font-semibold uppercase tracking-[0.2em] text-slate-500">Compared across</p>
      <div className="mt-4 flex flex-wrap items-center justify-center gap-3 sm:gap-4">
        {RETAILERS.map((r) => (
          <div
            key={r.id}
            className={`flex min-w-[7.5rem] items-center justify-center rounded-2xl bg-gradient-to-br ${r.bg} px-6 py-3.5 text-sm font-bold shadow-lg ${r.text} transition hover:scale-105 hover:shadow-xl`}
          >
            {r.name}
          </div>
        ))}
      </div>
    </div>
  );
}

function GlassSearch({
  q,
  setQ,
  busy,
  onSearch,
}: {
  q: string;
  setQ: (v: string) => void;
  busy: boolean;
  onSearch: (overrideQuery?: string) => void;
}) {
  return (
    <div className="mx-auto max-w-3xl px-4">
      <div className="group relative">
        <div className="absolute -inset-1 rounded-[1.35rem] bg-gradient-to-r from-emerald-400/40 via-teal-400/30 to-indigo-400/40 opacity-70 blur-lg transition group-hover:opacity-90" />
        <div className="relative flex flex-col gap-3 rounded-3xl border border-white/70 bg-white/50 p-2 shadow-2xl shadow-indigo-950/10 backdrop-blur-2xl sm:flex-row sm:items-center sm:pr-2">
          <div className="flex flex-1 items-center gap-3 rounded-2xl bg-white/60 px-4 py-1">
            <IconSearch className="h-5 w-5 shrink-0 text-emerald-600 animate-pulse-soft" />
            <input
              type="search"
              value={q}
              onChange={(e) => setQ(e.target.value)}
              onKeyDown={(e) => e.key === "Enter" && void onSearch()}
              placeholder="Search products across Amazon, Flipkart, Croma, Meesho…"
              className="w-full border-0 bg-transparent py-3.5 text-sm text-slate-900 placeholder:text-slate-400 focus:outline-none focus:ring-0"
            />
            <IconSparkles className="hidden h-5 w-5 shrink-0 text-indigo-500 sm:block animate-pulse-soft" />
          </div>
          <button
            type="button"
            disabled={busy}
            onClick={() => void onSearch()}
            className="flex items-center justify-center gap-2 rounded-2xl bg-gradient-to-r from-emerald-600 to-teal-600 px-8 py-3.5 text-sm font-semibold text-white shadow-lg transition hover:from-emerald-500 hover:to-teal-500 hover:shadow-xl disabled:opacity-50"
          >
            {busy ? (
              <>
                <span className="h-4 w-4 animate-spin rounded-full border-2 border-white/40 border-t-white" />
                Searching
              </>
            ) : (
              <>
                Compare prices
                <svg className="h-4 w-4" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2.5">
                  <path d="M5 12h14M13 6l6 6-6 6" strokeLinecap="round" strokeLinejoin="round" />
                </svg>
              </>
            )}
          </button>
        </div>
      </div>
      <div className="mt-4 flex flex-wrap justify-center gap-2">
        {POPULAR_CHIPS.map((chip) => (
          <button
            key={chip}
            type="button"
            onClick={() => void onSearch(chip)}
            className="rounded-full border border-slate-200/80 bg-white/70 px-4 py-2 text-xs font-medium text-slate-700 shadow-sm backdrop-blur transition hover:border-emerald-300 hover:bg-emerald-50/90 hover:text-emerald-900"
          >
            {chip}
          </button>
        ))}
      </div>
    </div>
  );
}

export default function App() {
  const [q, setQ] = useState("iPhone 15");
  const [busy, setBusy] = useState(false);
  const [err, setErr] = useState<string | null>(null);
  const [res, setRes] = useState<UnifiedSearchResponse | null>(null);

  const runSearch = async (overrideQuery?: string) => {
    const query = (overrideQuery ?? q).trim();
    if (!query) return;
    if (overrideQuery != null) setQ(overrideQuery);
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

  useEffect(() => {
    if (res?.groups?.length) {
      document.getElementById("search-results")?.scrollIntoView({ behavior: "smooth", block: "start" });
    }
  }, [res]);

  return (
    <div className="relative min-h-screen overflow-x-hidden bg-gradient-to-b from-slate-50 via-white to-emerald-50/30">
      <div className="pointer-events-none fixed inset-0 -z-10">
        <div className="absolute left-1/4 top-0 h-[420px] w-[420px] -translate-x-1/2 rounded-full bg-gradient-to-br from-emerald-300/25 via-teal-200/20 to-transparent blur-3xl" />
        <div className="absolute bottom-0 right-0 h-[380px] w-[380px] translate-x-1/4 rounded-full bg-gradient-to-tl from-indigo-300/20 via-violet-200/15 to-transparent blur-3xl" />
        <div className="absolute left-0 top-1/2 h-64 w-64 -translate-y-1/2 rounded-full bg-cyan-200/15 blur-3xl" />
      </div>

      <nav className="sticky top-0 z-50 border-b border-white/40 bg-white/55 shadow-sm backdrop-blur-xl">
        <div className="mx-auto flex max-w-6xl items-center justify-between gap-4 px-4 py-3 sm:px-6">
          <a href="#" className="flex items-center gap-3 transition hover:opacity-90">
            <SmartBasketLogo />
            <div>
              <span className="font-display text-lg font-bold tracking-tight text-slate-900">SmartBasket</span>
              <span className="ml-1.5 rounded-md bg-gradient-to-r from-emerald-600 to-indigo-600 px-1.5 py-0.5 text-[10px] font-bold uppercase tracking-wide text-white">
                AI
              </span>
              <p className="text-[11px] font-medium text-slate-500">Ecommerce price intelligence</p>
            </div>
          </a>
          <div className="hidden items-center gap-6 text-sm font-medium text-slate-600 sm:flex">
            <a href="#features" className="transition hover:text-emerald-700">
              Features
            </a>
            <a href="#search-results" className="rounded-full bg-slate-900/90 px-4 py-2 text-white shadow-md transition hover:bg-slate-800">
              Try search
            </a>
          </div>
        </div>
      </nav>

      <header className="relative mx-auto max-w-6xl px-4 pb-16 pt-10 sm:pb-24 sm:pt-14 lg:pt-20">
        <div className="grid items-center gap-12 lg:grid-cols-2">
          <div>
            <div className="inline-flex items-center gap-2 rounded-full border border-emerald-200/60 bg-emerald-50/80 px-4 py-1.5 text-xs font-semibold text-emerald-800 shadow-sm">
              <span className="relative flex h-2 w-2">
                <span className="absolute inline-flex h-full w-full animate-ping rounded-full bg-emerald-400 opacity-75" />
                <span className="relative inline-flex h-2 w-2 rounded-full bg-emerald-500" />
              </span>
              SBERT · FAISS · DistilBERT · Live multi-store
            </div>
            <h1 className="mt-6 font-display text-4xl font-extrabold leading-[1.1] tracking-tight text-slate-900 sm:text-5xl lg:text-[3.25rem]">
              Compare prices with{" "}
              <span className="text-gradient-brand">AI that understands</span> every listing
            </h1>
            <p className="mt-5 max-w-xl text-base leading-relaxed text-slate-600 sm:text-lg">
              SmartBasket unifies Amazon, Flipkart, Croma, and Meesho — matching semantically different titles,
              scoring delivery & offers, and surfacing where to buy with confidence.
            </p>
          </div>
          <HeroIllustration />
        </div>

        <div className="mt-12 sm:mt-16">
          <GlassSearch q={q} setQ={setQ} busy={busy} onSearch={runSearch} />
        </div>
        {err ? <p className="mx-auto mt-6 max-w-xl text-center text-sm font-medium text-rose-600">{err}</p> : null}
      </header>

      <div className="px-4 pb-10">
        <RetailerStrip />
      </div>

      <FeatureCards />

      <div id="search-results" className="scroll-mt-24 mx-auto max-w-6xl px-4 pb-20 pt-4">
        {res ? (
          <div className="space-y-10">
            <div className="flex items-end justify-between gap-4 border-b border-slate-200/80 pb-4">
              <div>
                <h2 className="font-display text-2xl font-bold text-slate-900">Your results</h2>
                <p className="mt-1 text-sm text-slate-600">
                  Query: <span className="font-semibold text-slate-800">{res.query}</span>
                </p>
              </div>
            </div>
            {res.groups.map((group) => (
              <section key={group.group_id} className="glass-strong rounded-3xl p-6 sm:p-8">
                <h2 className="font-display text-xl font-bold text-slate-900">{group.display_name}</h2>
                <h3 className="mt-6 text-xs font-bold uppercase tracking-wide text-slate-500">Price comparison</h3>
                <ComparisonTable group={group} />
                <h3 className="mt-8 text-xs font-bold uppercase tracking-wide text-slate-500">AI purchase recommendation</h3>
                <InsightCards group={group} />
                <div className="mt-4 rounded-2xl border border-emerald-200/60 bg-gradient-to-r from-emerald-50/90 to-teal-50/50 p-4">
                  <p className="text-sm leading-relaxed text-slate-800">
                    <span className="font-semibold text-emerald-800">Summary: </span>
                    {group.recommendation_summary}
                  </p>
                </div>
                <h3 className="mt-8 text-xs font-bold uppercase tracking-wide text-slate-500">Review sentiment (DistilBERT)</h3>
                <SentimentPerListing group={group} />
              </section>
            ))}
            {res.store_sentiment_rollups?.length ? (
              <section className="glass-strong rounded-3xl p-6 sm:p-8">
                <h2 className="font-display text-xl font-bold text-slate-900">Platform trust overview</h2>
                <p className="mt-1 text-sm text-slate-600">Aggregated sentiment and trust for this search.</p>
                <StoreRollups rows={res.store_sentiment_rollups} />
              </section>
            ) : null}
            {res.final_ai_recommendation ? (
              <section className="rounded-3xl border border-indigo-200/60 bg-gradient-to-br from-indigo-50/90 via-white to-sky-50/80 p-6 text-center shadow-lg sm:p-8">
                <h2 className="text-xs font-bold uppercase tracking-wide text-indigo-800">Final AI recommendation</h2>
                <p className="mx-auto mt-3 max-w-3xl text-sm leading-relaxed text-slate-800">{res.final_ai_recommendation}</p>
              </section>
            ) : null}
            <AlternativesSection data={res.alternatives} />
          </div>
        ) : (
          <div className="rounded-2xl border border-dashed border-slate-200/80 bg-white/30 py-12 text-center text-sm text-slate-500 backdrop-blur">
            Run a search above to see live comparison, AI picks, and semantic recommendations.
          </div>
        )}
      </div>

      <footer className="border-t border-white/50 bg-white/40 py-10 text-center backdrop-blur-lg">
        <div className="mx-auto flex max-w-6xl flex-col items-center gap-2 px-4">
          <div className="flex items-center gap-2">
            <SmartBasketLogo className="h-8 w-8" />
            <span className="font-display font-bold text-slate-900">SmartBasket AI</span>
          </div>
          <p className="max-w-md text-xs text-slate-500">
            Amazon · Flipkart · Croma · Meesho · SBERT · FAISS · DistilBERT — built for modern ecommerce teams.
          </p>
        </div>
      </footer>
    </div>
  );
}
