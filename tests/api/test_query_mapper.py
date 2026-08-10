from backend.api.query_mapper import to_query_response
from backend.generation.models import Citation, SourceReference
from backend.services.models import RAGServiceResult


def test_query_mapper_preserves_api_response_contract() -> None:
    result = RAGServiceResult(
        query="pipeline-normalized query",
        answer="A grounded answer [2][1].",
        citations=[
            Citation("2", "document-2", "chunk-2"),
            Citation("1", "document-1", "chunk-1"),
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
            ),
        ],
        model="synthetic-model",
        retrieval_latency_ms=12.5,
        context_build_latency_ms=2.25,
        generation_latency_ms=30.75,
        end_to_end_latency_ms=45.5,
    )

    response = to_query_response(result)

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


def test_query_mapper_allows_empty_sources_and_missing_timings() -> None:
    response = to_query_response(
        RAGServiceResult(
            query="Question without evidence",
            answer="I do not have enough evidence.",
            citations=[],
            sources=[],
            model="synthetic-model",
        )
    )

    assert response.citations == []
    assert response.sources == []
    assert response.metrics.model_dump() == {
        "retrieval_latency_ms": None,
        "context_build_latency_ms": None,
        "generation_latency_ms": None,
        "end_to_end_latency_ms": None,
    }
