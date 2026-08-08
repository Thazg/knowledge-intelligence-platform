from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any


@dataclass(frozen=True)
class SourceReference:
    citation_id: str
    document_id: str
    chunk_id: str
    title: str | None = None
    source: str | None = None
    url: str | None = None
    metadata: dict[str, Any] = field(default_factory=dict)


@dataclass(frozen=True)
class Citation:
    citation_id: str
    document_id: str
    chunk_id: str


@dataclass(frozen=True)
class GenerationContext:
    query: str
    context_text: str
    sources: list[SourceReference]
    token_count: int | None = None


@dataclass(frozen=True)
class GenerationResult:
    query: str
    answer: str
    citations: list[Citation]
    sources: list[SourceReference]

    model: str

    prompt_tokens: int | None = None
    completion_tokens: int | None = None
    total_tokens: int | None = None

    latency_ms: float | None = None

    metadata: dict[str, Any] = field(default_factory=dict)