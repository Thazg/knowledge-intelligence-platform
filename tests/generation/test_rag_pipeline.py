from dataclasses import dataclass, field
from typing import Any

from backend.generation.context_builder import ContextBuilder
from backend.generation.fake_generator import FakeGenerator
from backend.generation.rag_pipeline import RAGPipeline


@dataclass
class FakeRetrievalResult:
    document_id: str
    chunk_id: str
    content: str
    metadata: dict[str, Any] = field(default_factory=dict)


class FakeRetriever:
    def retrieve(
        self,
        query: str,
        top_k: int,
        **kwargs: object,
    ) -> list[FakeRetrievalResult]:
        return [
            FakeRetrievalResult(
                document_id="doc-1",
                chunk_id="chunk-1",
                content=(
                    "Kubernetes Deployments manage "
                    "replicated application workloads."
                ),
                metadata={
                    "title": "Kubernetes Documentation",
                    "source": "kubernetes",
                },
            )
        ][:top_k]


class EmptyRetriever:
    def retrieve(
        self,
        query: str,
        top_k: int,
        **kwargs: object,
    ) -> list[FakeRetrievalResult]:
        return []


def test_rag_pipeline_runs_end_to_end() -> None:
    pipeline = RAGPipeline(
        retriever=FakeRetriever(),  # type: ignore[arg-type]
        context_builder=ContextBuilder(
            max_context_tokens=1000,
            max_sources=8,
        ),
        generator=FakeGenerator(),
        top_k=10,
    )

    result = pipeline.run(
        "What does a Kubernetes Deployment manage?"
    )

    assert result.query == (
        "What does a Kubernetes Deployment manage?"
    )

    assert result.answer
    assert "[1]" in result.answer

    assert len(result.sources) == 1
    assert len(result.citations) == 1

    assert result.citations[0].citation_id == "1"
    assert result.citations[0].document_id == "doc-1"
    assert result.citations[0].chunk_id == "chunk-1"

    assert result.model == "fake-generator-v1"


def test_rag_pipeline_rejects_empty_query() -> None:
    pipeline = RAGPipeline(
        retriever=FakeRetriever(),  # type: ignore[arg-type]
        context_builder=ContextBuilder(),
        generator=FakeGenerator(),
    )

    try:
        pipeline.run("   ")
    except ValueError as exc:
        assert str(exc) == "query must not be empty"
    else:
        raise AssertionError("Expected ValueError")


def test_rag_pipeline_handles_no_retrieval_results() -> None:
    pipeline = RAGPipeline(
        retriever=EmptyRetriever(),  # type: ignore[arg-type]
        context_builder=ContextBuilder(),
        generator=FakeGenerator(),
    )

    result = pipeline.run("What is an unknown feature?")

    assert result.answer == (
        "The available evidence is insufficient "
        "to answer the question reliably."
    )
    assert result.citations == []
    assert result.sources == []
    assert result.metadata["grounded"] is False