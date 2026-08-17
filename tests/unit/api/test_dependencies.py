from __future__ import annotations

import subprocess
import sys
from pathlib import Path
from types import ModuleType
from typing import Any

import pytest

from backend.api import dependencies
from backend.core.config import Settings
from backend.retrieval.hybrid_retriever import HybridRetriever


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


def _cloud_settings(
    artifact_path: Path,
) -> Settings:
    return Settings(
        _env_file=None,
        rag_profile="cloud",
        qdrant_url="https://qdrant.example",
        qdrant_api_key="qdrant-secret",
        qdrant_collection="cloud_collection",
        bm25_query_artifact_path=artifact_path,
        groq_api_key="groq-secret",
        generation_model="groq-model",
        embedding_model="BAAI/bge-small-en-v1.5",
        dense_weight=0.7,
        bm25_weight=0.3,
        rrf_k=60,
    )


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
            calls["embedding_model"] = model_name

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
        qdrant_url="http://localhost:6333",
        qdrant_collection="local_collection",
        embedding_model="BAAI/bge-small-en-v1.5",
        dense_weight=0.7,
        bm25_weight=0.3,
        rrf_k=60,
    )

    retriever = dependencies._build_local_retriever(
        settings
    )

    assert isinstance(
        retriever,
        HybridRetriever,
    )
    assert calls["chunks_path"] == Path(
        "data/processed/chunks_fixed.jsonl"
    )
    assert calls["embedding_model"] == (
        "BAAI/bge-small-en-v1.5"
    )
    assert calls["vector_store"] == {
        "collection_name": "local_collection",
        "vector_size": 384,
        "url": "http://localhost:6333",
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

    artifact_path = tmp_path / "artifact.json"
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
            calls["encoder_path"] = path

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

    settings = _cloud_settings(
        artifact_path
    )

    retriever = dependencies._build_cloud_retriever(
        settings
    )

    assert isinstance(
        retriever,
        HybridRetriever,
    )
    assert calls["client"] == {
        "url": "https://qdrant.example",
        "api_key": "qdrant-secret",
    }
    assert calls["encoder_path"] == artifact_path

    assert calls["dense"]["collection_name"] == (
        "cloud_collection"
    )
    assert calls["dense"]["vector_name"] == (
        "dense_vector"
    )
    assert calls["dense"]["model_name"] == (
        "BAAI/bge-small-en-v1.5"
    )

    assert calls["bm25"]["collection_name"] == (
        "cloud_collection"
    )
    assert calls["bm25"]["vector_name"] == (
        "rank_bm25_sparse"
    )


def test_build_cloud_retriever_requires_existing_artifact(
    tmp_path: Path,
) -> None:
    missing_path = tmp_path / "missing.json"

    settings = _cloud_settings(
        missing_path
    )

    with pytest.raises(
        FileNotFoundError,
        match="BM25 query artifact not found",
    ):
        dependencies._build_cloud_retriever(
            settings
        )


def test_build_retriever_selects_local_profile(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    expected = object()

    monkeypatch.setattr(
        dependencies,
        "_build_local_retriever",
        lambda settings: expected,
    )

    settings = Settings(
        _env_file=None,
        rag_profile="local",
    )

    assert (
        dependencies._build_retriever(
            settings
        )
        is expected
    )


def test_build_retriever_selects_cloud_profile(
    monkeypatch: pytest.MonkeyPatch,
    tmp_path: Path,
) -> None:
    expected = object()

    monkeypatch.setattr(
        dependencies,
        "_build_cloud_retriever",
        lambda settings: expected,
    )

    artifact_path = tmp_path / "artifact.json"
    artifact_path.write_text(
        "{}",
        encoding="utf-8",
    )

    settings = _cloud_settings(
        artifact_path
    )

    assert (
        dependencies._build_retriever(
            settings
        )
        is expected
    )


def test_build_local_generator_preserves_existing_wiring(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    calls: dict[str, Any] = {}

    class FakeOllamaGenerator:
        def __init__(
            self,
            **kwargs: Any,
        ) -> None:
            calls.update(kwargs)

    import backend.generation.providers.ollama_generator as module

    monkeypatch.setattr(
        module,
        "OllamaGenerator",
        FakeOllamaGenerator,
    )

    settings = Settings(
        _env_file=None,
        rag_profile="local",
        generation_model="qwen3:4b-instruct",
        ollama_url="http://ollama:11434",
        generation_timeout_seconds=45.0,
        max_concurrent_generations=2,
    )

    generator = dependencies._build_local_generator(
        settings
    )

    assert isinstance(
        generator,
        FakeOllamaGenerator,
    )
    assert calls == {
        "model": "qwen3:4b-instruct",
        "base_url": "http://ollama:11434",
        "timeout_seconds": 45.0,
        "max_concurrent_generations": 2,
    }


def test_build_cloud_generator_uses_groq(
    monkeypatch: pytest.MonkeyPatch,
    tmp_path: Path,
) -> None:
    calls: dict[str, Any] = {}

    class FakeGroqGenerator:
        def __init__(
            self,
            **kwargs: Any,
        ) -> None:
            calls.update(kwargs)

    import backend.generation.providers.groq_generator as module

    monkeypatch.setattr(
        module,
        "GroqGenerator",
        FakeGroqGenerator,
    )

    artifact_path = tmp_path / "artifact.json"
    artifact_path.write_text(
        "{}",
        encoding="utf-8",
    )

    settings = _cloud_settings(
        artifact_path
    )

    generator = dependencies._build_cloud_generator(
        settings
    )

    assert isinstance(
        generator,
        FakeGroqGenerator,
    )
    assert calls == {
        "model": "groq-model",
        "api_key": "groq-secret",
        "timeout_seconds": 120.0,
        "max_concurrent_generations": 1,
    }


def test_build_generator_selects_local_profile(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    expected = object()

    monkeypatch.setattr(
        dependencies,
        "_build_local_generator",
        lambda settings: expected,
    )

    settings = Settings(
        _env_file=None,
        rag_profile="local",
    )

    assert (
        dependencies._build_generator(
            settings
        )
        is expected
    )


def test_build_generator_selects_cloud_profile(
    monkeypatch: pytest.MonkeyPatch,
    tmp_path: Path,
) -> None:
    expected = object()

    monkeypatch.setattr(
        dependencies,
        "_build_cloud_generator",
        lambda settings: expected,
    )

    artifact_path = tmp_path / "artifact.json"
    artifact_path.write_text(
        "{}",
        encoding="utf-8",
    )

    settings = _cloud_settings(
        artifact_path
    )

    assert (
        dependencies._build_generator(
            settings
        )
        is expected
    )