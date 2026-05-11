import logging
from threading import Lock
from typing import Optional

import numpy as np
from sentence_transformers import SentenceTransformer

from app.config import get_settings

_log = logging.getLogger(__name__)
_lock = Lock()
_model: Optional[SentenceTransformer] = None


def get_encoder() -> SentenceTransformer:
    global _model
    with _lock:
        if _model is None:
            settings = get_settings()
            _log.info("Loading SBERT: %s", settings.sbert_model)
            _model = SentenceTransformer(settings.sbert_model)
        return _model


def encode_texts(texts: list[str], batch_size: int = 32) -> np.ndarray:
    model = get_encoder()
    emb = model.encode(
        texts,
        batch_size=batch_size,
        show_progress_bar=False,
        convert_to_numpy=True,
        normalize_embeddings=True,
    )
    return np.asarray(emb, dtype=np.float32)


def product_to_text(title: str, description: str, category: str, brand: Optional[str]) -> str:
    parts = [title, description or "", f"category: {category}"]
    if brand:
        parts.append(f"brand: {brand}")
    return " \n ".join(p for p in parts if p)
