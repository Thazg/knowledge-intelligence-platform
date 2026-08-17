from __future__ import annotations

import subprocess
import sys
from pathlib import Path
from types import ModuleType
from typing import Any

import pytest

from backend.api import dependencies
from backend.core.config import Settings
from backend.retrieval.hybrid_retriever import (
    HybridRetriever,
)


def _fake_module(
    name: str,
    **attributes: Any,
) -> ModuleType:
    module = ModuleType(name)

    for key, value in attributes.items():
        setattr(
            module,
            key,
            value,
        )

    return module


def test_dependencies_import_does_not_load_heavy_retrieval_stacks() -> None:
    result = subprocess.run(
        [
            sys.executable,
            "-c",
            (
                "import sys; "
                "import backend.api.dependencies; "
                "print("
                "'torch' in sys.modules, "
                "'sentence_transformers' "
                "in sys.modules, "
                "'rank_bm25' in sys.modules, "
                "'fastembed' in sys.modules"
                ")"
            ),
        ],
        check=True,
        capture_output=True,
        text=True,
    )

    assert (
        result.stdout.strip()
        == "False False False False"
    )


def test_build_local_retriever_preserves_existing_wiring(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    calls: dict[str, Any] = {}

    class FakeSerializer:
        def load_jsonl(
            self,
            path: Path,
        ) -> list[str]:
            calls["chunks_path"] = path
            return ["chunk-a", "chunk-b"]

    class FakeEmbedder:
        dimension = 384

        def __init__(
            self,
            *,
            model_name: str,
        ) -> None:
            calls["embedding_model"] = (
                model_name
            )

    class FakeVectorStore:
        def __init__(
            self,
            **kwargs: Any,
        ) -> None:
            calls["vector_store"] = kwargs

    class FakeDense:
        def __init__(
            self,
            **kwargs: Any,
        ) -> None:
            calls["dense"] = kwargs

        def retrieve(
            self,
            *args: Any,
            **kwargs: Any,
        ) -> list[Any]:
            return []

    class FakeBM25:
        def __init__(
            self,
            **kwargs: Any,
        ) -> None:
            calls["bm25"] = kwargs

        def retrieve(
            self,
            *args: Any,
            **kwargs: Any,
        ) -> list[Any]:
            return []

    monkeypatch.setitem(
        sys.modules,
        "backend.chunking.serializer",
        _fake_module(
            "backend.chunking.serializer",
            ChunkSerializer=FakeSerializer,
        ),
    )
    monkeypatch.setitem(
        sys.modules,
        "backend.embedding.embedder",
        _fake_module(
            "backend.embedding.embedder",
            LocalEmbedder=FakeEmbedder,
        ),
    )
    monkeypatch.setitem(
        sys.modules,
        "backend.vector_store.qdrant_store",
        _fake_module(
            "backend.vector_store.qdrant_store",
            QdrantVectorStore=FakeVectorStore,
        ),
    )
    monkeypatch.setitem(
        sys.modules,
        "backend.retrieval.dense_retriever",
        _fake_module(
            "backend.retrieval.dense_retriever",
            DenseRetriever=FakeDense,
        ),
    )
    monkeypatch.setitem(
        sys.modules,
        "backend.retrieval.bm25_retriever",
        _fake_module(
            "backend.retrieval.bm25_retriever",
            BM25Retriever=FakeBM25,
        ),
    )

    settings = Settings(
        _env_file=None,
        chunks_path=Path(
            "data/processed/chunks_fixed.jsonl"
        ),
        qdrant_url=(
            "http://localhost:6333"
        ),
        qdrant_collection=(
            "local_collection"
        ),
        embedding_model=(
            "BAAI/bge-small-en-v1.5"
        ),
        dense_weight=0.7,
        bm25_weight=0.3,
        rrf_k=60,
    )

    retriever = (
        dependencies
        ._build_local_retriever(
            settings
        )
    )

    assert isinstance(
        retriever,
        HybridRetriever,
    )
    assert calls["chunks_path"] == (
        Path(
            "data/processed/"
            "chunks_fixed.jsonl"
        )
    )
    assert calls["embedding_model"] == (
        "BAAI/bge-small-en-v1.5"
    )
    assert calls["vector_store"] == {
        "collection_name": (
            "local_collection"
        ),
        "vector_size": 384,
        "url": (
            "http://localhost:6333"
        ),
    }
    assert calls["bm25"] == {
        "chunks": [
            "chunk-a",
            "chunk-b",
        ]
    }


def test_build_cloud_retriever_uses_cloud_components(
    monkeypatch: pytest.MonkeyPatch,
    tmp_path: Path,
) -> None:
    calls: dict[str, Any] = {}

    artifact_path = (
        tmp_path / "artifact.json"
    )
    artifact_path.write_text(
        "{}",
        encoding="utf-8",
    )

    class FakeQdrantClient:
        def __init__(
            self,
            **kwargs: Any,
        ) -> None:
            calls["client"] = kwargs

    class FakeDense:
        def __init__(
            self,
            **kwargs: Any,
        ) -> None:
            calls["dense"] = kwargs

        def retrieve(
            self,
            *args: Any,
            **kwargs: Any,
        ) -> list[Any]:
            return []

    class FakeEncoder:
        def __init__(
            self,
            path: Path,
        ) -> None:
            calls["encoder_path"] = (
                path
            )

        def encode(
            self,
            query: str,
        ) -> None:
            return None

    class FakeBM25:
        def __init__(
            self,
            **kwargs: Any,
        ) -> None:
            calls["bm25"] = kwargs

        def retrieve(
            self,
            *args: Any,
            **kwargs: Any,
        ) -> list[Any]:
            return []

    import qdrant_client
    import backend.retrieval.fastembed_cloud_dense_retriever as dense_module
    import backend.retrieval.rank_bm25_cloud_retriever as bm25_module
    import backend.retrieval.rank_bm25_query_encoder as encoder_module

    monkeypatch.setattr(
        qdrant_client,
        "QdrantClient",
        FakeQdrantClient,
    )
    monkeypatch.setattr(
        dense_module,
        "FastEmbedCloudDenseRetriever",
        FakeDense,
    )
    monkeypatch.setattr(
        encoder_module,
        "RankBM25QueryEncoder",
        FakeEncoder,
    )
    monkeypatch.setattr(
        bm25_module,
        "RankBM25CloudRetriever",
        FakeBM25,
    )

    settings = Settings(
        _env_file=None,
        rag_profile="cloud",
        qdrant_url=(
            "https://qdrant.example"
        ),
        qdrant_api_key=(
            "qdrant-secret"
        ),
        qdrant_collection=(
            "cloud_collection"
        ),
        bm25_query_artifact_path=(
            artifact_path
        ),
        groq_api_key="groq-secret",
        embedding_model=(
            "BAAI/bge-small-en-v1.5"
        ),
        dense_weight=0.7,
        bm25_weight=0.3,
        rrf_k=60,
    )

    retriever = (
        dependencies
        ._build_cloud_retriever(
            settings
        )
    )

    assert isinstance(
        retriever,
        HybridRetriever,
    )
    assert calls["client"] == {
        "url": (
            "https://qdrant.example"
        ),
        "api_key": (
            "qdrant-secret"
        ),
    }
    assert calls["encoder_path"] == (
        artifact_path
    )

    assert calls["dense"][
        "collection_name"
    ] == "cloud_collection"
    assert calls["dense"][
        "vector_name"
    ] == "dense_vector"
    assert calls["dense"][
        "model_name"
    ] == (
        "BAAI/bge-small-en-v1.5"
    )

    assert calls["bm25"][
        "collection_name"
    ] == "cloud_collection"
    assert calls["bm25"][
        "vector_name"
    ] == "rank_bm25_sparse"


def test_build_cloud_retriever_requires_existing_artifact(
    tmp_path: Path,
) -> None:
    missing_path = (
        tmp_path / "missing.json"
    )

    settings = Settings(
        _env_file=None,
        rag_profile="cloud",
        qdrant_api_key=(
            "qdrant-secret"
        ),
        bm25_query_artifact_path=(
            missing_path
        ),
        groq_api_key="groq-secret",
    )

    with pytest.raises(
        FileNotFoundError,
        match=(
            "BM25 query artifact "
            "not found"
        ),
    ):
        (
            dependencies
            ._build_cloud_retriever(
                settings
            )
        )


def test_get_rag_service_rejects_cloud_profile_until_generation_wiring(
    monkeypatch: pytest.MonkeyPatch,
    tmp_path: Path,
) -> None:
    artifact_path = (
        tmp_path / "artifact.json"
    )
    artifact_path.write_text(
        "{}",
        encoding="utf-8",
    )

    settings = Settings(
        _env_file=None,
        rag_profile="cloud",
        qdrant_api_key=(
            "qdrant-secret"
        ),
        bm25_query_artifact_path=(
            artifact_path
        ),
        groq_api_key="groq-secret",
    )

    monkeypatch.setattr(
        dependencies,
        "get_settings",
        lambda: settings,
    )

    dependencies.get_rag_service.cache_clear()

    try:
        with pytest.raises(
            RuntimeError,
            match=(
                "cloud RAG profile is not "
                "activated"
            ),
        ):
            dependencies.get_rag_service()
    finally:
        dependencies.get_rag_service.cache_clear()