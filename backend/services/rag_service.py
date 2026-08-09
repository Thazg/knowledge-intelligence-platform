from __future__ import annotations

import logging

from backend.api.schemas.query import (
    CitationResponse,
    MetricsResponse,
    QueryResponse,
    SourceResponse,
)
from backend.generation.rag_pipeline import RAGPipeline
from backend.core.metrics import (
    RAG_END_TO_END_DURATION_SECONDS,
    RAG_GENERATION_DURATION_SECONDS,
    RAG_QUERIES_TOTAL,
    RAG_QUERY_ERRORS_TOTAL,
    RAG_RETRIEVAL_DURATION_SECONDS,
)

logger = logging.getLogger(__name__)


class RAGService:
    def __init__(self, pipeline: RAGPipeline) -> None:
        self.pipeline = pipeline

    def query(self, query: str) -> QueryResponse:
        logger.info("RAG query started")

        try:
            result = self.pipeline.run(query)
        except Exception as exc:
            RAG_QUERIES_TOTAL.labels(
                status="error",
            ).inc()

            RAG_QUERY_ERRORS_TOTAL.labels(
                error_type=type(exc).__name__,
            ).inc()

            logger.exception("RAG query failed")

            raise

        metadata = result.metadata

        retrieval_latency_ms = metadata.get(
            "retrieval_latency_ms",
            0.0,
        )

        generation_latency_ms = metadata.get(
            "generation_stage_latency_ms",
            0.0,
        )

        end_to_end_latency_ms = metadata.get(
            "end_to_end_latency_ms",
            0.0,
        )

        RAG_QUERIES_TOTAL.labels(
            status="success",
        ).inc()

        RAG_RETRIEVAL_DURATION_SECONDS.observe(
            retrieval_latency_ms / 1000
        )

        RAG_GENERATION_DURATION_SECONDS.observe(
            generation_latency_ms / 1000
        )

        RAG_END_TO_END_DURATION_SECONDS.observe(
            end_to_end_latency_ms / 1000
        )

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
            retrieval_latency_ms,
            metadata.get("context_build_latency_ms", 0.0),
            generation_latency_ms,
            end_to_end_latency_ms,
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