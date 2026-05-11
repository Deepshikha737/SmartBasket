from fastapi import APIRouter, HTTPException

from app.ai.price_lstm import predict_next_price
from app.ai.price_xgb import predict_next_price_xgb
from app.api.deps import DbDep
from app.models.schemas import PredictionOut
from app.services.product_repository import ProductRepository

router = APIRouter(prefix="/api/predict", tags=["predict"])


@router.get("/price/{product_id}", response_model=PredictionOut)
async def predict_price(product_id: str, db: DbDep):
    repo = ProductRepository(db)
    series = await repo.price_series(product_id, limit=48)
    p = await repo.get(product_id)
    if not p:
        raise HTTPException(404, "Product not found")
    lstm_p = predict_next_price(series) if len(series) >= 2 else p.price
    xgb_p = predict_next_price_xgb(series) if len(series) >= 5 else None
    if xgb_p is not None:
        pred = round((lstm_p + xgb_p) / 2.0, 2)
        note = "Ensemble of LSTM sequence head and XGBoost on sliding windows of price_history."
        model = "LSTM+XGBoost"
    else:
        pred = round(lstm_p, 2)
        note = "LSTM only (need ≥5 history points for XGBoost window model)."
        model = "PriceLSTM"
    return PredictionOut(
        product_id=product_id,
        predicted_next_price=pred,
        lstm_price=round(lstm_p, 2),
        xgboost_price=round(xgb_p, 2) if xgb_p is not None else None,
        confidence_note=note,
        model=model,
    )
