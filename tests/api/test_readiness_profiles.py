from __future__ import annotations

from pathlib import Path
from typing import Any

import pytest
from fastapi.testclient import TestClient

import backend.api.app as app_module
from backend.core.config import Settings


client = TestClient(
    app_module.app
)


class FakeResponse:
    def __init__(
        self,
        payload: dict[str, Any] | None = None,
    ) -> None:
        self._payload = payload or {}

    def raise_for_status(self) -> None:
        return None

    def json(self) -> dict[str, Any]:
        return self._payload


def _cloud_settings(
    tmp_path: Path,
) -> Settings:
    return Settings(
        _env_file=None,
        rag_profile="cloud",
        qdrant_url="https://qdrant.example",
        qdrant_api_key="qdrant-secret",
        qdrant_collection=(
            "enterprise_knowledge_cloud_"
            "bge_rank_bm25_v1"
        ),
        bm25_query_artifact_path=(
            tmp_path / "artifact.json"
        ),
        groq_api_key="groq-secret",
        generation_model="groq-model",
    )


def test_cloud_ready_checks_qdrant_collection_and_groq_models(
    monkeypatch: pytest.MonkeyPatch,
    tmp_path: Path,
) -> None:
    settings = _cloud_settings(
        tmp_path
    )

    calls: list[
        tuple[
            str,
            dict[str, str] | None,
        ]
    ] = []

    def fake_get(
        url: str,
        *,
        timeout: float,
        headers: dict[str, str] | None = None,
    ) -> FakeResponse:
        assert timeout == 2.0

        calls.append(
            (
                url,
                headers,
            )
        )

        if url == (
            "https://qdrant.example/"
            "collections/"
            "enterprise_knowledge_cloud_"
            "bge_rank_bm25_v1"
        ):
            return FakeResponse(
                {
                    "status": "ok",
                }
            )

        if url == app_module.GROQ_MODELS_URL:
            return FakeResponse(
                {
                    "data": [
                        {
                            "id": "groq-model",
                        }
                    ]
                }
            )

        raise AssertionError(
            f"Unexpected URL: {url}"
        )

    monkeypatch.setattr(
        app_module,
        "get_settings",
        lambda: settings,
    )
    monkeypatch.setattr(
        app_module,
        "get_rag_service",
        lambda: object(),
    )
    monkeypatch.setattr(
        app_module.httpx,
        "get",
        fake_get,
    )

    response = client.get(
        "/ready"
    )

    assert response.status_code == 200
    assert response.json() == {
        "status": "ready",
        "dependencies": {
            "rag_service": "ready",
            "qdrant": "ready",
            "groq": "ready",
        },
    }

    assert calls == [
        (
            (
                "https://qdrant.example/"
                "collections/"
                "enterprise_knowledge_cloud_"
                "bge_rank_bm25_v1"
            ),
            {
                "api-key": (
                    "qdrant-secret"
                )
            },
        ),
        (
            app_module.GROQ_MODELS_URL,
            {
                "Authorization": (
                    "Bearer groq-secret"
                ),
                "Content-Type": (
                    "application/json"
                ),
            },
        ),
    ]

    assert all(
        "/api/tags" not in url
        for url, _ in calls
    )


def test_cloud_ready_returns_503_when_groq_model_is_missing(
    monkeypatch: pytest.MonkeyPatch,
    tmp_path: Path,
) -> None:
    settings = _cloud_settings(
        tmp_path
    )

    def fake_get(
        url: str,
        *,
        timeout: float,
        headers: dict[str, str] | None = None,
    ) -> FakeResponse:
        assert timeout == 2.0
        assert headers is not None

        if url.startswith(
            "https://qdrant.example/"
        ):
            return FakeResponse(
                {
                    "status": "ok",
                }
            )

        if url == app_module.GROQ_MODELS_URL:
            return FakeResponse(
                {
                    "data": [],
                }
            )

        raise AssertionError(
            f"Unexpected URL: {url}"
        )

    monkeypatch.setattr(
        app_module,
        "get_settings",
        lambda: settings,
    )
    monkeypatch.setattr(
        app_module,
        "get_rag_service",
        lambda: object(),
    )
    monkeypatch.setattr(
        app_module.httpx,
        "get",
        fake_get,
    )

    response = client.get(
        "/ready"
    )

    assert response.status_code == 503
    assert response.json() == {
        "status": "not_ready",
        "dependencies": {
            "rag_service": "ready",
            "qdrant": "ready",
            "groq": "unavailable",
        },
    }


def test_cloud_ready_returns_503_when_qdrant_is_unavailable(
    monkeypatch: pytest.MonkeyPatch,
    tmp_path: Path,
) -> None:
    settings = _cloud_settings(
        tmp_path
    )

    def fake_get(
        url: str,
        *,
        timeout: float,
        headers: dict[str, str] | None = None,
    ) -> FakeResponse:
        assert timeout == 2.0
        assert headers is not None

        if url.startswith(
            "https://qdrant.example/"
        ):
            raise RuntimeError(
                "qdrant unavailable"
            )

        if url == app_module.GROQ_MODELS_URL:
            return FakeResponse(
                {
                    "data": [
                        {
                            "id": "groq-model",
                        }
                    ]
                }
            )

        raise AssertionError(
            f"Unexpected URL: {url}"
        )

    monkeypatch.setattr(
        app_module,
        "get_settings",
        lambda: settings,
    )
    monkeypatch.setattr(
        app_module,
        "get_rag_service",
        lambda: object(),
    )
    monkeypatch.setattr(
        app_module.httpx,
        "get",
        fake_get,
    )

    response = client.get(
        "/ready"
    )

    assert response.status_code == 503
    assert response.json() == {
        "status": "not_ready",
        "dependencies": {
            "rag_service": "ready",
            "qdrant": "unavailable",
            "groq": "ready",
        },
    }