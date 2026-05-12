from functools import lru_cache

from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file=".env", env_file_encoding="utf-8", extra="ignore")

    app_name: str = "PCS API"
    debug: bool = False

    mongodb_uri: str = "mongodb://localhost:27017"
    mongodb_db: str = "price_comparison"

    # Sentence transformer model (small for faster cold start; swap in prod)
    sbert_model: str = "sentence-transformers/all-MiniLM-L6-v2"

    # FAISS index path (persisted under data/)
    faiss_index_path: str = "data/faiss_index.bin"
    faiss_meta_path: str = "data/faiss_meta.json"

    # DistilBERT sentiment
    sentiment_model: str = "distilbert-base-uncased-finetuned-sst-2-english"

    cors_origins: str = "http://localhost:5173,http://127.0.0.1:5173"


@lru_cache
def get_settings() -> Settings:
    return Settings()
