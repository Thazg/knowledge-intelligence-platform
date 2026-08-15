from __future__ import annotations

from typing import Annotated

from pydantic import BaseModel, Field, StringConstraints


QueryText = Annotated[
    str,
    StringConstraints(
        strip_whitespace=True,
        min_length=1,
        max_length=1024,
    ),
]


class QueryRequest(BaseModel):
    query: QueryText = Field(
        ...,
        description="User question to answer using the RAG pipeline.",
    )


class CitationResponse(BaseModel):
    citation_id: str
    document_id: str
    chunk_id: str


class SourceResponse(BaseModel):
    citation_id: str
    document_id: str
    chunk_id: str
    title: str | None = None
    source: str | None = None
    url: str | None = None


class MetricsResponse(BaseModel):
    retrieval_latency_ms: float | None = None
    context_build_latency_ms: float | None = None
    generation_latency_ms: float | None = None
    end_to_end_latency_ms: float | None = None


class QueryResponse(BaseModel):
    query: str
    answer: str
    citations: list[CitationResponse]
    sources: list[SourceResponse]
    model: str
    metrics: MetricsResponse