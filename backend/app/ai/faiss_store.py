import json
import logging
import os
from pathlib import Path
from typing import Optional

import faiss
import numpy as np

from app.config import get_settings

_log = logging.getLogger(__name__)


class FaissProductIndex:
    """Inner-product index on L2-normalized vectors == cosine similarity."""

    def __init__(self) -> None:
        self._index: Optional[faiss.IndexFlatIP] = None
        self._ids: list[str] = []
        self._dim: int = 0

    @property
    def ready(self) -> bool:
        return self._index is not None and len(self._ids) > 0

    def build(self, vectors: np.ndarray, ids: list[str]) -> None:
        if vectors.ndim != 2:
            raise ValueError("vectors must be 2D")
        if len(ids) != vectors.shape[0]:
            raise ValueError("ids length must match vectors rows")
        self._dim = vectors.shape[1]
        self._ids = list(ids)
        self._index = faiss.IndexFlatIP(self._dim)
        faiss.normalize_L2(vectors)
        self._index.add(vectors)

    def search(self, query_vec: np.ndarray, top_k: int) -> list[tuple[str, float]]:
        if not self.ready or self._index is None:
            return []
        q = query_vec.reshape(1, -1).astype(np.float32)
        faiss.normalize_L2(q)
        scores, idxs = self._index.search(q, min(top_k, len(self._ids)))
        out: list[tuple[str, float]] = []
        for i, s in zip(idxs[0], scores[0]):
            if i < 0:
                continue
            out.append((self._ids[i], float(s)))
        return out

    def persist(self) -> None:
        settings = get_settings()
        path = Path(settings.faiss_index_path)
        meta_path = Path(settings.faiss_meta_path)
        path.parent.mkdir(parents=True, exist_ok=True)
        if self._index is None:
            return
        faiss.write_index(self._index, str(path))
        with open(meta_path, "w", encoding="utf-8") as f:
            json.dump({"ids": self._ids, "dim": self._dim}, f)

    def load(self) -> bool:
        settings = get_settings()
        path = Path(settings.faiss_index_path)
        meta_path = Path(settings.faiss_meta_path)
        if not path.exists() or not meta_path.exists():
            return False
        with open(meta_path, encoding="utf-8") as f:
            meta = json.load(f)
        self._ids = list(meta["ids"])
        self._dim = int(meta["dim"])
        self._index = faiss.read_index(str(path))
        _log.info("Loaded FAISS index: %s vectors dim=%s", len(self._ids), self._dim)
        return True


_store = FaissProductIndex()


def get_faiss_store() -> FaissProductIndex:
    return _store
