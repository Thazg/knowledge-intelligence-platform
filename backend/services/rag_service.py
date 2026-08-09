from __future__ import annotations

import logging

from backend.api.schemas.query import (
    CitationResponse,
    MetricsResponse,
    QueryResponse,
    SourceResponse,
)
from backend.generation.rag_pipeline import RAGPipeline


logger = logging.getLogger(__name__)


class RAGService:
    def __init__(self, pipeline: RAGPipeline) -> None:
        self.pipeline = pipeline

    def query(self, query: str) -> QueryResponse:
        logger.info("RAG query started")

        result = self.pipeline.run(query)

        metadata = result.metadata

        logger.info(
            (
                "RAG query completed "
                "retrieval_latency_ms=%.2f "
                "context_build_latency_ms=%.2f "
                "generation_latency_ms=%.2f "
                "end_to_end_latency_ms=%.2f "
                "retrieved_results=%s "
                "context_sources=%s "
                "cited_sources=%s"
            ),
            metadata.get("retrieval_latency_ms", 0.0),
            metadata.get("context_build_latency_ms", 0.0),
            metadata.get("generation_stage_latency_ms", 0.0),
            metadata.get("end_to_end_latency_ms", 0.0),
            metadata.get("retrieved_results"),
            metadata.get("context_sources"),
            metadata.get("cited_sources"),
        )

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
            retrieval_latency_ms=metadata.get(
                "retrieval_latency_ms"
            ),
            context_build_latency_ms=metadata.get(
                "context_build_latency_ms"
            ),
            generation_latency_ms=metadata.get(
                "generation_stage_latency_ms"
            ),
            end_to_end_latency_ms=metadata.get(
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