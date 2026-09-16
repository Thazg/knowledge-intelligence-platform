from __future__ import annotations

import json
from collections.abc import Iterator

import pytest
from fastapi.testclient import TestClient

from backend.api.app import app
from backend.api.dependencies import get_rag_service
from backend.core.errors import DependencyTimeoutError
from backend.generation.models import Citation, SourceReference
from backend.services.models import (
    RAGServiceResult,
    RAGServiceStreamEvent,
)

client = TestClient(app)


def _result(query: str) -> RAGServiceResult:
    return RAGServiceResult(
        query=query,
        answer=(
            "BuildKit improves Docker image builds [1]."
        ),
        citations=[
            Citation(
                citation_id="1",
                document_id="doc-1",
                chunk_id="chunk-1",
            ),
        ],
        sources=[
            SourceReference(
                citation_id="1",
                document_id="doc-1",
                chunk_id="chunk-1",
                title="BuildKit",
                source="docker",
                url=(
                    "https://docs.docker.com/"
                    "build/buildkit/"
                ),
            ),
        ],
        model="fake-stream-model",
        retrieval_latency_ms=10.0,
        context_build_latency_ms=2.0,
        generation_latency_ms=20.0,
        end_to_end_latency_ms=32.0,
    )


class FakeStreamingRAGService:
    def query(self, query: str) -> RAGServiceResult:
        return _result(query)

    def stream(
        self,
        query: str,
    ) -> Iterator[RAGServiceStreamEvent]:
        yield RAGServiceStreamEvent(
            event="status",
            status="retrieving",
        )
        yield RAGServiceStreamEvent(
            event="status",
            status="generating",
        )
        yield RAGServiceStreamEvent(
            event="answer_delta",
            delta="BuildKit improves ",
        )
        yield RAGServiceStreamEvent(
            event="answer_delta",
            delta="Docker image builds [1].",
        )
        yield RAGServiceStreamEvent(
            event="done",
            result=_result(query),
        )


class FakeTimeoutStreamingRAGService:
    def stream(
        self,
        query: str,
    ) -> Iterator[RAGServiceStreamEvent]:
        yield RAGServiceStreamEvent(
            event="status",
            status="retrieving",
        )
        raise DependencyTimeoutError("groq")


@pytest.fixture(autouse=True)
def use_fake_streaming_service():
    app.dependency_overrides[get_rag_service] = (
        lambda: FakeStreamingRAGService()
    )

    yield

    app.dependency_overrides.clear()


def _events(response_text: str) -> list[tuple[str, dict]]:
    events: list[tuple[str, dict]] = []
    normalized = response_text.replace(
        "\r\n",
        "\n",
    )

    for block in normalized.strip().split(
        "\n\n"
    ):
        lines = block.splitlines()
        event = lines[0].removeprefix(
            "event: "
        )
        data = json.loads(
            lines[1].removeprefix("data: ")
        )
        events.append((event, data))

    return events


def test_stream_query_returns_ordered_sse_events() -> None:
    response = client.post(
        "/v1/query/stream",
        json={
            "query": (
                "What is Docker BuildKit?"
            ),
        },
    )

    assert response.status_code == 200
    assert response.headers[
        "content-type"
    ].startswith("text/event-stream")

    events = _events(response.text)

    assert [event for event, _ in events] == [
        "status",
        "status",
        "answer_delta",
        "answer_delta",
        "citations",
        "done",
    ]
    assert events[0][1] == {
        "status": "retrieving",
    }
    assert events[1][1] == {
        "status": "generating",
    }
    assert "".join(
        data["delta"]
        for event, data in events
        if event == "answer_delta"
    ) == (
        "BuildKit improves Docker image builds [1]."
    )


def test_stream_query_emits_existing_citation_schema() -> None:
    response = client.post(
        "/v1/query/stream",
        json={
            "query": "What is Docker BuildKit?",
        },
    )

    citations = next(
        data
        for event, data in _events(response.text)
        if event == "citations"
    )

    assert citations == {
        "citations": [
            {
                "citation_id": "1",
                "document_id": "doc-1",
                "chunk_id": "chunk-1",
            }
        ],
        "sources": [
            {
                "citation_id": "1",
                "document_id": "doc-1",
                "chunk_id": "chunk-1",
                "title": "BuildKit",
                "source": "docker",
                "url": (
                    "https://docs.docker.com/"
                    "build/buildkit/"
                ),
            }
        ],
    }


def test_stream_query_preserves_request_validation() -> None:
    response = client.post(
        "/v1/query/stream",
        json={
            "query": "   ",
        },
    )

    assert response.status_code == 422


def test_stream_query_normalizes_dependency_errors() -> None:
    app.dependency_overrides[get_rag_service] = (
        lambda: FakeTimeoutStreamingRAGService()
    )

    response = client.post(
        "/v1/query/stream",
        json={
            "query": "What is Docker BuildKit?",
        },
    )

    events = _events(response.text)

    assert [event for event, _ in events] == [
        "status",
        "error",
    ]
    assert events[-1][1] == {
        "code": "generation_timeout",
        "message": (
            "Answer generation timed out. Please retry."
        ),
        "retryable": True,
    }
    assert "groq" not in response.text


def test_existing_query_endpoint_remains_compatible() -> None:
    response = client.post(
        "/v1/query",
        json={
            "query": "What is Docker BuildKit?",
        },
    )

    assert response.status_code == 200
    assert response.json()["answer"] == (
        "BuildKit improves Docker image builds [1]."
    )
