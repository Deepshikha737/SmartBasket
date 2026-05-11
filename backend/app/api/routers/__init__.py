from fastapi import APIRouter

from app.api.routers import admin, alerts, compare, health, predict, products, recommend, search, sentiment

api_router = APIRouter()
api_router.include_router(health.router)
api_router.include_router(products.router)
api_router.include_router(search.router)
api_router.include_router(compare.router)
api_router.include_router(recommend.router)
api_router.include_router(sentiment.router)
api_router.include_router(alerts.router)
api_router.include_router(predict.router)
api_router.include_router(admin.router)
