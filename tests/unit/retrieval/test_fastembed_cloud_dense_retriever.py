from __future__ import annotations

import sys
from types import SimpleNamespace
from typing import Any

import pytest

from backend.retrieval.fastembed_cloud_dense_retriever import (
    FastEmbedCloudDenseRetriever,
)


def _point(
    *,
    chunk_id: str,
    document_id: str,
    score: float,
    content: str = "content",
    source: str = "kubernetes",
    filename: str = "doc.md",
    relative_path: str = "docs/doc.md",
    chunk_index: int = 0,
    token_count: int = 10,
    title: str | None = "Title",
) -> SimpleNamespace:
    return SimpleNamespace(
        score=score,
        payload={
            "chunk_id": chunk_id,
            "document_id": document_id,
            "content": content,
            "source": source,
            "filename": filename,
            "relative_path": relative_path,
            "chunk_index": chunk_index,
            "token_count": token_count,
            "title": title,
        },
    )


class FakeEmbedding:
    def __init__(
        self,
        values: list[float],
    ) -> None:
        self.values = values

    def tolist(self) -> list[float]:
        return list(self.values)


class FakeModel:
    def __init__(
        self,
        embedding: list[float],
    ) -> None:
        self.embedding = embedding
        self.calls: list[list[str]] = []

    def query_embed(
        self,
        documents: list[str],
    ) -> list[FakeEmbedding]:
        self.calls.append(documents)

        return [
            FakeEmbedding(
                self.embedding
            )
        ]


class EmptyFakeModel:
    def query_embed(
        self,
        documents: list[str],
    ) -> list[FakeEmbedding]:
        return []


class FakeQdrantClient:
    def __init__(
        self,
        points: list[SimpleNamespace],
    ) -> None:
        self.points = points
        self.calls: list[dict[str, Any]] = []

    def query_points(
        self,
        **kwargs: Any,
    ) -> SimpleNamespace:
        self.calls.append(kwargs)

        limit = int(kwargs["limit"])

        return SimpleNamespace(
            points=self.points[:limit]
        )


def _retriever(
    client: FakeQdrantClient,
    *,
    model: FakeModel | EmptyFakeModel | None = None,
) -> FastEmbedCloudDenseRetriever:
    return FastEmbedCloudDenseRetriever(
        client=client,
        collection_name="cloud_collection",
        vector_name="dense_vector",
        model_name=(
            "BAAI/bge-small-en-v1.5"
        ),
        model=(
            model
            if model is not None
            else FakeModel(
                [0.1, 0.2, 0.3]
            )
        ),
    )


def test_module_import_does_not_load_fastembed() -> None:
    import subprocess

    result = subprocess.run(
        [
            sys.executable,
            "-c",
            (
                "import sys; "
                "import backend.retrieval."
                "fastembed_cloud_dense_retriever; "
                "print('fastembed' in sys.modules)"
            ),
        ],
        check=True,
        capture_output=True,
        text=True,
    )

    assert result.stdout.strip() == "False"


def test_retrieve_embeds_query_and_queries_named_vector() -> None:
    model = FakeModel(
        [0.1, 0.2, 0.3]
    )
    client = FakeQdrantClient(
        [
            _point(
                chunk_id="chunk-1",
                document_id="doc-1",
                score=0.9,
            )
        ]
    )

    results = _retriever(
        client,
        model=model,
    ).retrieve(
        "What is Kubernetes?",
        top_k=1,
    )

    assert len(results) == 1
    assert model.calls == [
        ["What is Kubernetes?"]
    ]

    call = client.calls[0]

    assert call["collection_name"] == (
        "cloud_collection"
    )
    assert call["query"] == pytest.approx(
        [0.1, 0.2, 0.3]
    )
    assert call["using"] == "dense_vector"
    assert call["limit"] == 1
    assert call["with_payload"] is True


def test_retrieve_maps_payload_to_result() -> None:
    client = FakeQdrantClient(
        [
            _point(
                chunk_id="chunk-1",
                document_id="doc-1",
                score=0.75,
                content="Deployment content",
                source="kubernetes",
                filename="deployment.md",
                relative_path=(
                    "content/en/docs/deployment.md"
                ),
                chunk_index=3,
                token_count=128,
                title="Deployments",
            )
        ]
    )

    result = _retriever(
        client
    ).retrieve(
        "deployment",
        top_k=1,
    )[0]

    assert result.chunk_id == "chunk-1"
    assert result.document_id == "doc-1"
    assert result.content == (
        "Deployment content"
    )
    assert result.score == pytest.approx(
        0.75
    )
    assert result.rank == 1
    assert result.source == "kubernetes"
    assert result.filename == (
        "deployment.md"
    )
    assert result.relative_path == (
        "content/en/docs/deployment.md"
    )
    assert result.chunk_index == 3
    assert result.token_count == 128
    assert result.title == "Deployments"


def test_retrieve_applies_score_threshold() -> None:
    client = FakeQdrantClient(
        [
            _point(
                chunk_id="low",
                document_id="doc-1",
                score=0.4,
            ),
            _point(
                chunk_id="high",
                document_id="doc-2",
                score=0.8,
            ),
        ]
    )

    results = _retriever(
        client
    ).retrieve(
        "query",
        top_k=2,
        score_threshold=0.5,
    )

    assert [
        result.chunk_id
        for result in results
    ] == ["high"]
    assert results[0].rank == 1


def test_retrieve_expands_candidate_pool_before_document_filtering() -> None:
    client = FakeQdrantClient(
        [
            _point(
                chunk_id="chunk-a1",
                document_id="doc-a",
                score=0.9,
            ),
            _point(
                chunk_id="chunk-a2",
                document_id="doc-a",
                score=0.8,
            ),
            _point(
                chunk_id="chunk-b1",
                document_id="doc-b",
                score=0.7,
            ),
            _point(
                chunk_id="chunk-c1",
                document_id="doc-c",
                score=0.6,
            ),
        ]
    )

    results = _retriever(
        client
    ).retrieve(
        "query",
        top_k=2,
        max_chunks_per_document=1,
        candidate_multiplier=3,
    )

    assert client.calls[0]["limit"] == 6
    assert [
        result.chunk_id
        for result in results
    ] == [
        "chunk-a1",
        "chunk-b1",
    ]
    assert [
        result.rank
        for result in results
    ] == [1, 2]


@pytest.mark.parametrize(
    (
        "query",
        "top_k",
        "max_chunks",
        "multiplier",
    ),
    [
        ("   ", 5, None, 3),
        ("query", 0, None, 3),
        ("query", 5, 0, 3),
        ("query", 5, None, 0),
    ],
)
def test_retrieve_rejects_invalid_arguments(
    query: str,
    top_k: int,
    max_chunks: int | None,
    multiplier: int,
) -> None:
    retriever = _retriever(
        FakeQdrantClient([])
    )

    with pytest.raises(ValueError):
        retriever.retrieve(
            query,
            top_k=top_k,
            max_chunks_per_document=max_chunks,
            candidate_multiplier=multiplier,
        )


@pytest.mark.parametrize(
    (
        "collection",
        "vector",
        "model_name",
    ),
    [
        ("", "dense", "model"),
        ("collection", "", "model"),
        ("collection", "dense", ""),
    ],
)
def test_constructor_rejects_empty_configuration(
    collection: str,
    vector: str,
    model_name: str,
) -> None:
    with pytest.raises(ValueError):
        FastEmbedCloudDenseRetriever(
            client=FakeQdrantClient([]),
            collection_name=collection,
            vector_name=vector,
            model_name=model_name,
            model=FakeModel(
                [0.1]
            ),
        )


def test_retrieve_rejects_empty_embedding_result() -> None:
    retriever = _retriever(
        FakeQdrantClient([]),
        model=EmptyFakeModel(),
    )

    with pytest.raises(
        RuntimeError,
        match=(
            "FastEmbed returned no "
            "query embedding"
        ),
    ):
        retriever.retrieve(
            "query"
        )