from __future__ import annotations

from pathlib import Path

import pytest

from pydantic import ValidationError

from backend.core.config import Settings


def test_generation_timeout_defaults_to_120_seconds(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    monkeypatch.delenv(
        "GENERATION_TIMEOUT_SECONDS",
        raising=False,
    )

    settings = Settings(
        _env_file=None,
    )

    assert (
        settings.generation_timeout_seconds
        == 120.0
    )


def test_generation_timeout_can_be_loaded_from_environment(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    monkeypatch.setenv(
        "GENERATION_TIMEOUT_SECONDS",
        "45",
    )

    settings = Settings(
        _env_file=None,
    )

    assert (
        settings.generation_timeout_seconds
        == 45.0
    )


@pytest.mark.parametrize(
    "timeout_seconds",
    [
        0.0,
        -1.0,
    ],
)
def test_generation_timeout_must_be_positive(
    timeout_seconds: float,
) -> None:
    with pytest.raises(ValidationError):
        Settings(
            _env_file=None,
            generation_timeout_seconds=timeout_seconds,
        )


def test_retrieval_weights_cannot_both_be_zero() -> None:
    with pytest.raises(
        ValidationError,
        match=(
            "retrieval weights cannot "
            "both be zero"
        ),
    ):
        Settings(
            _env_file=None,
            dense_weight=0.0,
            bm25_weight=0.0,
        )


def test_retrieval_weights_can_disable_dense() -> None:
    settings = Settings(
        _env_file=None,
        dense_weight=0.0,
        bm25_weight=1.0,
    )

    assert settings.dense_weight == 0.0
    assert settings.bm25_weight == 1.0


def test_retrieval_weights_can_disable_bm25() -> None:
    settings = Settings(
        _env_file=None,
        dense_weight=1.0,
        bm25_weight=0.0,
    )

    assert settings.dense_weight == 1.0
    assert settings.bm25_weight == 0.0


def test_max_concurrent_generations_defaults_to_one() -> None:
    settings = Settings(
        _env_file=None,
    )

    assert (
        settings.max_concurrent_generations
        == 1
    )


@pytest.mark.parametrize(
    "value",
    [
        0,
        -1,
    ],
)
def test_max_concurrent_generations_must_be_positive(
    value: int,
) -> None:
    with pytest.raises(
        ValidationError,
    ):
        Settings(
            _env_file=None,
            max_concurrent_generations=value,
        )


def test_rag_profile_defaults_to_local() -> None:
    settings = Settings(
        _env_file=None,
    )

    assert settings.rag_profile == "local"


def test_local_profile_does_not_require_cloud_settings() -> None:
    settings = Settings(
        _env_file=None,
        rag_profile="local",
        qdrant_api_key=None,
        bm25_query_artifact_path=None,
        groq_api_key=None,
    )

    assert settings.rag_profile == "local"


def test_cloud_profile_requires_cloud_settings(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    monkeypatch.delenv(
        "QDRANT_API_KEY",
        raising=False,
    )
    monkeypatch.delenv(
        "BM25_QUERY_ARTIFACT_PATH",
        raising=False,
    )
    monkeypatch.delenv(
        "GROQ_API_KEY",
        raising=False,
    )

    with pytest.raises(
        ValidationError,
        match=(
            "cloud profile requires: "
            "QDRANT_API_KEY, "
            "BM25_QUERY_ARTIFACT_PATH, "
            "GROQ_API_KEY"
        ),
    ):
        Settings(
            _env_file=None,
            rag_profile="cloud",
        )


def test_cloud_profile_accepts_required_settings() -> None:
    artifact_path = Path(
        "artifacts/retrieval/"
        "rank-bm25-query-artifact-v1.json"
    )

    settings = Settings(
        _env_file=None,
        rag_profile="cloud",
        qdrant_api_key="qdrant-secret",
        bm25_query_artifact_path=artifact_path,
        groq_api_key="groq-secret",
    )

    assert settings.rag_profile == "cloud"
    assert (
        settings.bm25_query_artifact_path
        == artifact_path
    )


def test_cloud_profile_can_be_loaded_from_environment(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    monkeypatch.setenv(
        "RAG_PROFILE",
        "cloud",
    )
    monkeypatch.setenv(
        "QDRANT_API_KEY",
        "qdrant-secret",
    )
    monkeypatch.setenv(
        "BM25_QUERY_ARTIFACT_PATH",
        (
            "artifacts/retrieval/"
            "rank-bm25-query-artifact-v1.json"
        ),
    )
    monkeypatch.setenv(
        "GROQ_API_KEY",
        "groq-secret",
    )

    settings = Settings(
        _env_file=None,
    )

    assert settings.rag_profile == "cloud"
    assert (
        settings.bm25_query_artifact_path
        == Path(
            "artifacts/retrieval/"
            "rank-bm25-query-artifact-v1.json"
        )
    )


def test_rag_profile_rejects_unknown_value() -> None:
    with pytest.raises(
        ValidationError,
    ):
        Settings(
            _env_file=None,
            rag_profile="unsupported",
        )