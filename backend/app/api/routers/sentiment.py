from fastapi import APIRouter, HTTPException

from app.ai.sentiment import analyze_batch
from app.api.deps import DbDep
from app.models.schemas import SentimentRequest, SentimentResult
from app.services.product_repository import ProductRepository

router = APIRouter(prefix="/api/sentiment", tags=["sentiment"])


@router.post("", response_model=list[SentimentResult])
async def sentiment(body: SentimentRequest, db: DbDep):
    texts: list[str] = []
    if body.texts:
        texts = body.texts
    elif body.product_id:
        repo = ProductRepository(db)
        texts = await repo.get_reviews(body.product_id)
    else:
        raise HTTPException(400, "Provide texts or product_id")
    if not texts:
        return []
    raw = analyze_batch(texts[:40])
    out: list[SentimentResult] = []
    for t, r in zip(texts[:40], raw):
        label = str(r["label"]).upper()
        if label not in ("POSITIVE", "NEGATIVE"):
            label = "POSITIVE" if label == "LABEL_1" else "NEGATIVE"
        out.append(
            SentimentResult(
                label=label,  # type: ignore[arg-type]
                score=float(r["score"]),
                text_preview=t[:120],
            )
        )
    return out
