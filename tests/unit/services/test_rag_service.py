from __future__ import annotations

import pytest

from backend.generation.models import Citation, GenerationResult, SourceReference
from backend.services.rag_service import RAGService


class StubPipeline:
    def __init__(
        self,
        result: GenerationResult | None = None,
        error: Exception | None = None,
    ) -> None:
        self.result = result
        self.error = error
        self.queries: list[str] = []

    def run(self, query: str) -> GenerationResult:
        self.queries.append(query)

        if self.error is not None:
            raise self.error

        if self.result is None:
            raise AssertionError("StubPipeline requires a result or error")

        return self.result


def test_query_maps_pipeline_result_to_api_response() -> None:
    pipeline_result = GenerationResult(
        query="pipeline-normalized query",
        answer="A grounded answer [2][1].",
        citations=[
            Citation(
                citation_id="2",
                document_id="document-2",
                chunk_id="chunk-2",
            ),
            Citation(
                citation_id="1",
                document_id="document-1",
                chunk_id="chunk-1",
            ),
        ],
        sources=[
            SourceReference(
                citation_id="1",
                document_id="document-1",
                chunk_id="chunk-1",
                title="First source",
                source="docker",
                url="https://example.test/first",
                metadata={"relative_path": "docker/first.md"},
            ),
            SourceReference(
                citation_id="2",
                document_id="document-2",
                chunk_id="chunk-2",
                title="Second source",
                source="kubernetes",
                url=None,
            ),
        ],
        model="synthetic-model",
        prompt_tokens=101,
        completion_tokens=23,
        total_tokens=124,
        latency_ms=777.0,
        metadata={
            "retrieval_latency_ms": 12.5,
            "context_build_latency_ms": 2.25,
            "generation_stage_latency_ms": 30.75,
            "generation_latency_ms": 999.0,
            "end_to_end_latency_ms": 45.5,
            "retrieved_results": 4,
            "context_sources": 2,
            "cited_sources": 2,
        },
    )
    pipeline = StubPipeline(result=pipeline_result)
    service = RAGService(pipeline=pipeline)

    response = service.query("  original request query  ")

    assert pipeline.queries == ["  original request query  "]
    assert response.model_dump() == {
        "query": "pipeline-normalized query",
        "answer": "A grounded answer [2][1].",
        "citations": [
            {
                "citation_id": "2",
                "document_id": "document-2",
                "chunk_id": "chunk-2",
            },
            {
                "citation_id": "1",
                "document_id": "document-1",
                "chunk_id": "chunk-1",
            },
        ],
        "sources": [
            {
                "citation_id": "1",
                "document_id": "document-1",
                "chunk_id": "chunk-1",
                "title": "First source",
                "source": "docker",
                "url": "https://example.test/first",
            },
            {
                "citation_id": "2",
                "document_id": "document-2",
                "chunk_id": "chunk-2",
                "title": "Second source",
                "source": "kubernetes",
                "url": None,
            },
        ],
        "model": "synthetic-model",
        "metrics": {
            "retrieval_latency_ms": 12.5,
            "context_build_latency_ms": 2.25,
            "generation_latency_ms": 30.75,
            "end_to_end_latency_ms": 45.5,
        },
    }


def test_query_allows_empty_citations_sources_and_metadata() -> None:
    pipeline = StubPipeline(
        result=GenerationResult(
            query="Question without evidence",
            answer="I do not have enough evidence.",
            citations=[],
            sources=[],
            model="synthetic-model",
        )
    )
    service = RAGService(pipeline=pipeline)

    response = service.query("Question without evidence")

    assert response.model_dump() == {
        "query": "Question without evidence",
        "answer": "I do not have enough evidence.",
        "citations": [],
        "sources": [],
        "model": "synthetic-model",
        "metrics": {
            "retrieval_latency_ms": None,
            "context_build_latency_ms": None,
            "generation_latency_ms": None,
            "end_to_end_latency_ms": None,
        },
    }


def test_query_propagates_pipeline_exception_unchanged() -> None:
    pipeline_error = RuntimeError("synthetic pipeline failure")
    pipeline = StubPipeline(error=pipeline_error)
    service = RAGService(pipeline=pipeline)

    with pytest.raises(RuntimeError) as exc_info:
        service.query("failing query")

    assert exc_info.value is pipeline_error
    assert pipeline.queries == ["failing query"]
