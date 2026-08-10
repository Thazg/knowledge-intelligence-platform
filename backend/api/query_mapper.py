from __future__ import annotations

from backend.api.schemas.query import (
    CitationResponse,
    MetricsResponse,
    QueryResponse,
    SourceResponse,
)
from backend.services.models import RAGServiceResult


def to_query_response(result: RAGServiceResult) -> QueryResponse:
    return QueryResponse(
        query=result.query,
        answer=result.answer,
        citations=[
            CitationResponse(
                citation_id=citation.citation_id,
                document_id=citation.document_id,
                chunk_id=citation.chunk_id,
            )
            for citation in result.citations
        ],
        sources=[
            SourceResponse(
                citation_id=source.citation_id,
                document_id=source.document_id,
                chunk_id=source.chunk_id,
                title=source.title,
                source=source.source,
                url=source.url,
            )
            for source in result.sources
        ],
        model=result.model,
        metrics=MetricsResponse(
            retrieval_latency_ms=result.retrieval_latency_ms,
            context_build_latency_ms=result.context_build_latency_ms,
            generation_latency_ms=result.generation_latency_ms,
            end_to_end_latency_ms=result.end_to_end_latency_ms,
        ),
    )
