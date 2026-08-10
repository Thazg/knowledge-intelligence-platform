from __future__ import annotations

from dataclasses import dataclass

from backend.generation.models import Citation, SourceReference


@dataclass(frozen=True)
class RAGServiceResult:
    query: str
    answer: str
    citations: list[Citation]
    sources: list[SourceReference]
    model: str
    retrieval_latency_ms: float | None = None
    context_build_latency_ms: float | None = None
    generation_latency_ms: float | None = None
    end_to_end_latency_ms: float | None = None
