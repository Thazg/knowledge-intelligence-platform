from __future__ import annotations

import pytest

from fastapi.testclient import TestClient

from backend.api.app import app
from backend.api.dependencies import get_rag_service
from backend.core.errors import (
    DependencyResponseError,
    DependencyTimeoutError,
    DependencyUnavailableError,
)
from backend.generation.models import Citation, SourceReference
from backend.services.models import RAGServiceResult


client = TestClient(app)


class FakeRAGService:
    def query(self, query: str) -> RAGServiceResult:
        return RAGServiceResult(
            query=query,
            answer=(
                "A Kubernetes Deployment manages "
                "replicated Pods [1]."
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
                    title="Deployments",
                    source="kubernetes",
                    url=None,
                ),
            ],
            model="fake-model",
            retrieval_latency_ms=10.0,
            context_build_latency_ms=1.0,
            generation_latency_ms=20.0,
            end_to_end_latency_ms=31.0,
        )


class FakeQdrantFailureService:
    def query(self, query: str) -> RAGServiceResult:
        raise DependencyUnavailableError(
            "qdrant"
        )


class FakeOllamaFailureService:
    def query(self, query: str) -> RAGServiceResult:
        raise DependencyUnavailableError(
            "ollama"
        )


class FakeOllamaHTTPFailureService:
    def query(self, query: str) -> RAGServiceResult:
        raise DependencyResponseError(
            "ollama"
        )


class FakeOllamaTimeoutService:
    def query(self, query: str) -> RAGServiceResult:
        raise DependencyTimeoutError(
            "ollama"
        )


@pytest.fixture(autouse=True)
def use_fake_rag_service():
    app.dependency_overrides[get_rag_service] = (
        lambda: FakeRAGService()
    )

    yield

    app.dependency_overrides.clear()


def test_health_returns_ok() -> None:
    response = client.get("/health")

    assert response.status_code == 200
    assert response.json() == {
        "status": "ok",
    }


def test_ready_returns_200_when_dependencies_are_ready(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    class FakeResponse:
        def __init__(
            self,
            payload: dict | None = None,
        ) -> None:
            self._payload = payload or {}

        def raise_for_status(self) -> None:
            return None

        def json(self) -> dict:
            return self._payload

    def fake_get(
        url: str,
        timeout: float,
    ) -> FakeResponse:
        if url.endswith("/api/tags"):
            return FakeResponse(
                {
                    "models": [
                        {
                            "name": "qwen3:4b-instruct",
                        },
                    ],
                }
            )

        return FakeResponse()

    monkeypatch.setattr(
        "backend.api.app.get_rag_service",
        lambda: FakeRAGService(),
    )

    monkeypatch.setattr(
        "backend.api.app.httpx.get",
        fake_get,
    )

    response = client.get("/ready")

    assert response.status_code == 200
    assert response.json() == {
        "status": "ready",
        "dependencies": {
            "rag_service": "ready",
            "qdrant": "ready",
            "ollama": "ready",
        },
    }


def test_ready_returns_503_when_generation_model_is_missing(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    class FakeResponse:
        def __init__(
            self,
            payload: dict | None = None,
        ) -> None:
            self._payload = payload or {}

        def raise_for_status(self) -> None:
            return None

        def json(self) -> dict:
            return self._payload

    def fake_get(
        url: str,
        timeout: float,
    ) -> FakeResponse:
        if url.endswith("/api/tags"):
            return FakeResponse(
                {
                    "models": [],
                }
            )

        return FakeResponse()

    monkeypatch.setattr(
        "backend.api.app.get_rag_service",
        lambda: FakeRAGService(),
    )

    monkeypatch.setattr(
        "backend.api.app.httpx.get",
        fake_get,
    )

    response = client.get("/ready")

    assert response.status_code == 503
    assert response.json() == {
        "status": "not_ready",
        "dependencies": {
            "rag_service": "ready",
            "qdrant": "ready",
            "ollama": "unavailable",
        },
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


def test_query_rejects_whitespace_only_query() -> None:
    response = client.post(
        "/v1/query",
        json={
            "query": "   ",
        },
    )

    assert response.status_code == 422


def test_query_returns_rag_response() -> None:
    response = client.post(
        "/v1/query",
        json={
            "query": "What is a Kubernetes Deployment?",
        },
    )

    assert response.status_code == 200

    body = response.json()

    assert body["query"] == (
        "What is a Kubernetes Deployment?"
    )

    assert body["answer"] == (
        "A Kubernetes Deployment manages "
        "replicated Pods [1]."
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
        "detail": (
            "A required backend service is unavailable."
        ),
    }


def test_query_returns_503_when_backend_returns_http_error() -> None:
    app.dependency_overrides[get_rag_service] = (
        lambda: FakeOllamaHTTPFailureService()
    )

    try:
        response = client.post(
            "/v1/query",
            json={
                "query": (
                    "How do Kubernetes Deployments work?"
                ),
            },
        )
    finally:
        app.dependency_overrides.clear()

    assert response.status_code == 503
    assert response.json() == {
        "detail": (
            "A required backend service returned an error."
        ),
    }


def test_query_returns_503_when_backend_times_out() -> None:
    app.dependency_overrides[get_rag_service] = (
        lambda: FakeOllamaTimeoutService()
    )

    try:
        response = client.post(
            "/v1/query",
            json={
                "query": (
                    "How do Kubernetes Deployments work?"
                ),
            },
        )
    finally:
        app.dependency_overrides.clear()

    assert response.status_code == 503
    assert response.json() == {
        "detail": (
            "A required backend service timed out."
        ),
    }


def test_request_id_header_is_echoed() -> None:
    response = client.post(
        "/v1/query",
        json={
            "query": "What is Kubernetes?",
        },
        headers={
            "X-Request-ID": "e2e-test-001",
        },
    )

    assert response.status_code == 200

    assert (
        response.headers["X-Request-ID"]
        == "e2e-test-001"
    )


def test_query_strips_surrounding_whitespace() -> None:
    response = client.post(
        "/v1/query",
        json={
            "query": "  What is Kubernetes?  ",
        },
    )

    assert response.status_code == 200

    assert (
        response.json()["query"]
        == "What is Kubernetes?"
    )