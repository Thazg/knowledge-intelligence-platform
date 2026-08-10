from __future__ import annotations

import logging

from backend.generation.rag_pipeline import RAGPipeline
from backend.core.metrics import (
    RAG_END_TO_END_DURATION_SECONDS,
    RAG_GENERATION_DURATION_SECONDS,
    RAG_QUERIES_TOTAL,
    RAG_QUERY_ERRORS_TOTAL,
    RAG_RETRIEVAL_DURATION_SECONDS,
)
from backend.services.models import RAGServiceResult

logger = logging.getLogger(__name__)


class RAGService:
    def __init__(self, pipeline: RAGPipeline) -> None:
        self.pipeline = pipeline

    def query(self, query: str) -> RAGServiceResult:
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

        return RAGServiceResult(
            query=result.query,
            answer=result.answer,
            citations=list(result.citations),
            sources=list(result.sources),
            model=result.model,
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
