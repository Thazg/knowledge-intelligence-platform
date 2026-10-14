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

    assert (
        context.sources[0].excerpt
        == "FastAPI supports dependency injection."
    )
    assert (
        context.sources[1].excerpt
        == "Kubernetes Deployments manage replicated applications."
    )

    assert "[SOURCE 1]" in context.context_text
    assert "[SOURCE 2]" in context.context_text
    assert "FastAPI supports dependency injection." in context.context_text
    assert context.token_count is not None
    assert context.token_count > 0


def test_context_builder_truncates_long_excerpts() -> None:
    long_content = "x" * 600

    builder = ContextBuilder(
        max_context_tokens=10000,
        max_sources=8,
    )

    context = builder.build(
        query="What is x?",
        results=[
            FakeRetrievalResult(
                document_id="doc-1",
                chunk_id="chunk-1",
                content=long_content,
            ),
        ],  # type: ignore[arg-type]
    )

    assert len(context.sources) == 1
    assert context.sources[0].excerpt == "x" * 500
    assert long_content in context.context_text


def test_context_builder_cleans_excerpt_display_noise() -> None:
    builder = ContextBuilder(
        max_context_tokens=10000,
        max_sources=8,
    )

    context = builder.build(
        query="How do I generate text?",
        results=[
            FakeRetrievalResult(
                document_id="doc-1",
                chunk_id="chunk-1",
                content=(
                    "<!--Copyright 2024 Example-->\n"
                    "Use `generate()`.\n"
                    "```py\n"
                    "model.generate()\n"
                    "```\n\n\n"
                    "Done."
                ),
            ),
        ],  # type: ignore[arg-type]
    )

    assert len(context.sources) == 1

    excerpt = context.sources[0].excerpt

    assert excerpt is not None
    assert "Copyright" not in excerpt
    assert "```" not in excerpt
    assert "\n\n\n" not in excerpt
    assert "Use `generate()`." in excerpt


def test_context_builder_links_original_file_and_hides_front_matter() -> None:
    builder = ContextBuilder(max_context_tokens=10000)
    context = builder.build(
        query="What is BuildKit?",
        results=[
            FakeRetrievalResult(
                document_id="doc-1",
                chunk_id="chunk-1",
                content=(
                    "---\n"
                    "title: Multi-stage builds\n"
                    "description: Build Docker images\n"
                    "---\n"
                    "# Multi-stage builds\n"
                    "Copy artifacts into the runtime image."
                ),
                metadata={
                    "source": "docker",
                    "relative_path": (
                        "content/get-started/docker-concepts/"
                        "building-images/multi-stage-builds.md"
                    ),
                    "title": "Multi-stage builds { #multi-stage-builds }",
                },
            )
        ],  # type: ignore[arg-type]
    )

    source = context.sources[0]
    assert source.title == "Multi-stage builds"
    assert source.url == (
        "https://github.com/docker/docs/blob/main/"
        "content/get-started/docker-concepts/"
        "building-images/multi-stage-builds.md"
    )
    assert source.excerpt == (
        "# Multi-stage builds\n"
        "Copy artifacts into the runtime image."
    )
    assert "description: Build Docker images" in context.context_text


def test_context_builder_keeps_explicit_source_url() -> None:
    builder = ContextBuilder(max_context_tokens=10000)
    context = builder.build(
        query="What is BuildKit?",
        results=[
            FakeRetrievalResult(
                document_id="doc-1",
                chunk_id="chunk-1",
                content="BuildKit builds images.",
                metadata={
                    "source": "docker",
                    "relative_path": "content/buildkit.md",
                    "url": "https://docs.docker.com/build/buildkit/",
                },
            )
        ],  # type: ignore[arg-type]
    )
    assert context.sources[0].url == (
        "https://docs.docker.com/build/buildkit/"
    )


def test_context_builder_summarizes_front_matter_only_chunk() -> None:
    builder = ContextBuilder(max_context_tokens=10000)
    context = builder.build(
        query="What does Qdrant document?",
        results=[
            FakeRetrievalResult(
                document_id="doc-1",
                chunk_id="chunk-1",
                content=(
                    "---\n"
                    "title: Documentation\n"
                    'short_description: "Build with Qdrant and FastAPI."\n'
                    "content:\n"
                    "  - partial: documentation/banner\n"
                ),
            )
        ],  # type: ignore[arg-type]
    )

    assert context.sources[0].excerpt == (
        "Document summary: Build with Qdrant and FastAPI."
    )
    assert "partial: documentation/banner" in context.context_text
