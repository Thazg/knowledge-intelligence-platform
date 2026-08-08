from dataclasses import dataclass, field
from typing import Any

from backend.generation.context_builder import ContextBuilder


@dataclass
class FakeRetrievalResult:
    document_id: str
    chunk_id: str
    content: str
    metadata: dict[str, Any] = field(default_factory=dict)


def test_context_builder_builds_context() -> None:
    results = [
        FakeRetrievalResult(
            document_id="doc-1",
            chunk_id="chunk-1",
            content="FastAPI supports dependency injection.",
            metadata={
                "title": "FastAPI Documentation",
                "source": "fastapi",
            },
        ),
        FakeRetrievalResult(
            document_id="doc-2",
            chunk_id="chunk-2",
            content="Kubernetes Deployments manage replicated applications.",
            metadata={
                "title": "Kubernetes Documentation",
                "source": "kubernetes",
            },
        ),
    ]

    builder = ContextBuilder(
        max_context_tokens=1000,
        max_sources=8,
    )

    context = builder.build(
        query="How can FastAPI be deployed on Kubernetes?",
        results=results,  # type: ignore[arg-type]
    )

    assert len(context.sources) == 2
    assert context.sources[0].citation_id == "1"
    assert context.sources[1].citation_id == "2"

    assert "[SOURCE 1]" in context.context_text
    assert "[SOURCE 2]" in context.context_text
    assert "FastAPI supports dependency injection." in context.context_text
    assert context.token_count is not None
    assert context.token_count > 0