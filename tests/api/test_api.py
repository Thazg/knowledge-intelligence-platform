from __future__ import annotations

import httpx
import pytest

from fastapi.testclient import TestClient
from qdrant_client.http.exceptions import ResponseHandlingException

from backend.api.app import app
from backend.api.dependencies import get_rag_service
from backend.api.schemas.query import (
    CitationResponse,
    MetricsResponse,
    QueryResponse,
    SourceResponse,
)


client = TestClient(app)


class FakeRAGService:
    def query(self, query: str) -> QueryResponse:
        return QueryResponse(
            query=query,
            answer="A Kubernetes Deployment manages replicated Pods [1].",
            citations=[
                CitationResponse(
                    citation_id="1",
                    document_id="doc-1",
                    chunk_id="chunk-1",
                ),
            ],
            sources=[
                SourceResponse(
                    citation_id="1",
                    document_id="doc-1",
                    chunk_id="chunk-1",
                    title="Deployments",
                    source="kubernetes",
                    url=None,
                ),
            ],
            model="fake-model",
            metrics=MetricsResponse(
                retrieval_latency_ms=10.0,
                context_build_latency_ms=1.0,
                generation_latency_ms=20.0,
                end_to_end_latency_ms=31.0,
            ),
        )


class FakeQdrantFailureService:
    def query(self, query: str) -> QueryResponse:
        raise ResponseHandlingException(
            httpx.ConnectError("Qdrant unavailable")
        )


class FakeOllamaFailureService:
    def query(self, query: str) -> QueryResponse:
        raise httpx.ConnectError("Ollama unavailable")


@pytest.fixture(autouse=True)
def use_fake_rag_service() -> None:
    app.dependency_overrides[get_rag_service] = lambda: FakeRAGService()

    yield

    app.dependency_overrides.clear()


def test_health_returns_ok() -> None:
    response = client.get("/health")

    assert response.status_code == 200
    assert response.json() == {
        "status": "ok",
    }


def test_query_rejects_empty_query() -> None:
    response = client.post(
        "/v1/query",
        json={
            "query": "",
        },
    )

    assert response.status_code == 422


def test_query_rejects_missing_query() -> None:
    response = client.post(
        "/v1/query",
        json={},
    )

    assert response.status_code == 422


def test_query_returns_rag_response() -> None:
    app.dependency_overrides[get_rag_service] = lambda: FakeRAGService()

    try:
        response = client.post(
            "/v1/query",
            json={
                "query": "What is a Kubernetes Deployment?",
            },
        )
    finally:
        app.dependency_overrides.clear()

    assert response.status_code == 200

    body = response.json()

    assert body["query"] == "What is a Kubernetes Deployment?"

    assert body["answer"] == (
        "A Kubernetes Deployment manages replicated Pods [1]."
    )

    assert body["model"] == "fake-model"

    assert body["citations"] == [
        {
            "citation_id": "1",
            "document_id": "doc-1",
            "chunk_id": "chunk-1",
        },
    ]

    assert body["sources"] == [
        {
            "citation_id": "1",
            "document_id": "doc-1",
            "chunk_id": "chunk-1",
            "title": "Deployments",
            "source": "kubernetes",
            "url": None,
        },
    ]

    assert body["metrics"] == {
        "retrieval_latency_ms": 10.0,
        "context_build_latency_ms": 1.0,
        "generation_latency_ms": 20.0,
        "end_to_end_latency_ms": 31.0,
    }


def test_query_returns_503_when_qdrant_is_unavailable() -> None:
    app.dependency_overrides[get_rag_service] = (
        lambda: FakeQdrantFailureService()
    )

    try:
        response = client.post(
            "/v1/query",
            json={
                "query": "What is Kubernetes?",
            },
        )
    finally:
        app.dependency_overrides.clear()

    assert response.status_code == 503
    assert response.json() == {
        "detail": "Vector database is unavailable.",
    }


def test_query_returns_503_when_ollama_is_unavailable() -> None:
    app.dependency_overrides[get_rag_service] = (
        lambda: FakeOllamaFailureService()
    )

    try:
        response = client.post(
            "/v1/query",
            json={
                "query": "What is Kubernetes?",
            },
        )
    finally:
        app.dependency_overrides.clear()

    assert response.status_code == 503
    assert response.json() == {
        "detail": "A required backend service is unavailable.",
    }
