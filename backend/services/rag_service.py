from __future__ import annotations

from backend.api.schemas.query import (
    CitationResponse,
    MetricsResponse,
    QueryResponse,
    SourceResponse,
)
from backend.generation.rag_pipeline import RAGPipeline


class RAGService:
    def __init__(self, pipeline: RAGPipeline) -> None:
        self.pipeline = pipeline

    def query(self, query: str) -> QueryResponse:
        result = self.pipeline.run(query)

        citations = [
            CitationResponse(
                citation_id=citation.citation_id,
                document_id=citation.document_id,
                chunk_id=citation.chunk_id,
            )
            for citation in result.citations
        ]

        sources = [
            SourceResponse(
                citation_id=source.citation_id,
                document_id=source.document_id,
                chunk_id=source.chunk_id,
                title=source.title,
                source=source.source,
                url=source.url,
            )
            for source in result.sources
        ]

        metrics = MetricsResponse(
            retrieval_latency_ms=result.metadata.get(
                "retrieval_latency_ms"
            ),
            context_build_latency_ms=result.metadata.get(
                "context_build_latency_ms"
            ),
            generation_latency_ms=result.metadata.get(
                "generation_stage_latency_ms"
            ),
            end_to_end_latency_ms=result.metadata.get(
                "end_to_end_latency_ms"
            ),
        )

        return QueryResponse(
            query=result.query,
            answer=result.answer,
            citations=citations,
            sources=sources,
            model=result.model,
            metrics=metrics,
        )