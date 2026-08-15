from __future__ import annotations

from functools import lru_cache
from pathlib import Path

from pydantic import Field
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        extra="ignore",
        case_sensitive=False,
    )

    # Infrastructure
    qdrant_url: str = "http://localhost:6333"
    ollama_url: str = "http://localhost:11434"

    # Data
    chunks_path: Path = Path("data/processed/chunks_fixed.jsonl")

    # Vector store / embeddings
    qdrant_collection: str = "enterprise_knowledge_fixed_bge_small"
    embedding_model: str = "BAAI/bge-small-en-v1.5"

    # Generation
    generation_model: str = "qwen3:4b-instruct"
    generation_timeout_seconds: float = Field(
        default=120.0,
        gt=0,
    )

    # Retrieval
    dense_weight: float = Field(default=0.7, ge=0.0)
    bm25_weight: float = Field(default=0.3, ge=0.0)
    rrf_k: int = Field(default=60, gt=0)
    retrieval_top_k: int = Field(default=10, gt=0)

    # Context
    max_context_tokens: int = Field(default=4000, gt=0)
    max_context_sources: int = Field(default=6, gt=0)


@lru_cache(maxsize=1)
def get_settings() -> Settings:
    return Settings()