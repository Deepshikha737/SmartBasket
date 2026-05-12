import logging
from contextlib import asynccontextmanager

from apscheduler.schedulers.asyncio import AsyncIOScheduler
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.ai.faiss_store import get_faiss_store
from app.api.routers import api_router
from app.config import get_settings
from app.db.mongo import close_db, get_db
from app.services.alerts_service import check_alerts_once, ensure_alert_baselines
from app.services.catalog_cleanup import purge_disallowed_products
from app.services.product_repository import ProductRepository

logging.basicConfig(level=logging.INFO)
_log = logging.getLogger(__name__)

scheduler = AsyncIOScheduler()


async def _alert_tick() -> None:
    db = await get_db()
    await ensure_alert_baselines(db)
    events = await check_alerts_once(db)
    for ev in events:
        _log.warning("Price alert triggered: %s", ev)


@asynccontextmanager
async def lifespan(app: FastAPI):
    settings = get_settings()
    db = await get_db()
    repo = ProductRepository(db)
    await repo.ensure_indexes()
    await purge_disallowed_products(db)
    await ensure_alert_baselines(db)
    loaded = get_faiss_store().load()
    _log.info("FAISS preload: %s", "ok" if loaded else "no index on disk")

    scheduler.add_job(_alert_tick, "interval", minutes=2, id="price_alerts", max_instances=1)
    scheduler.start()
    await _alert_tick()

    yield

    scheduler.shutdown(wait=False)
    await close_db()


def create_app() -> FastAPI:
    settings = get_settings()
    app = FastAPI(title=settings.app_name, lifespan=lifespan)
    origins = [o.strip() for o in settings.cors_origins.split(",") if o.strip()]
    app.add_middleware(
        CORSMiddleware,
        allow_origins=origins or ["*"],
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )
    app.include_router(api_router)
    return app


app = create_app()
