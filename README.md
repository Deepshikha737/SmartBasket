# PCS — AI Ecommerce Price Comparison

Monorepo: **FastAPI + MongoDB + FAISS + Sentence Transformers + DistilBERT** backend, **React + Tailwind** dashboard, **Docker Compose** for local runs.

## Quick start (local)

1. Start MongoDB (local install or Docker): port `27017`.
2. Backend:

```bash
cd backend
python -m venv .venv
.venv\Scripts\activate
pip install -r requirements.txt
copy .env.example .env
uvicorn app.main:app --reload --host 0.0.0.0 --port 8000
```

First run downloads SBERT and DistilBERT weights (several hundred MB).

3. Frontend:

```bash
cd frontend
npm install
npm run dev
```

Open `http://localhost:5173` and search; the app compares **Amazon, Flipkart, Croma, and Meesho** (adapter layer — plug in live APIs in `platform_adapters.py`).

## Docker

From the repo root:

```bash
docker compose up --build
```

Dashboard: `http://localhost:8080` · API: `http://localhost:8000/docs`

## Documentation

See [docs/ARCHITECTURE.md](docs/ARCHITECTURE.md) for APIs, schema, AI flows, and scaling notes.
