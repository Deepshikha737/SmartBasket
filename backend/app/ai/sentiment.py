import logging
from threading import Lock
from typing import Optional

from transformers import pipeline

from app.config import get_settings

_log = logging.getLogger(__name__)
_lock = Lock()
_pipe = None


def get_sentiment_pipeline():
    global _pipe
    with _lock:
        if _pipe is None:
            settings = get_settings()
            _log.info("Loading sentiment model: %s", settings.sentiment_model)
            _pipe = pipeline(
                "sentiment-analysis",
                model=settings.sentiment_model,
                tokenizer=settings.sentiment_model,
                device=-1,
            )
        return _pipe


def analyze_batch(texts: list[str], max_length: int = 256) -> list[dict]:
    pipe = get_sentiment_pipeline()
    truncated = [t[:max_length] for t in texts if t.strip()]
    if not truncated:
        return []
    return pipe(truncated)
