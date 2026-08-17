from __future__ import annotations

import subprocess
import sys
from types import SimpleNamespace
from typing import Any

import pytest
from qdrant_client import models

from backend.retrieval.rank_bm25_cloud_retriever import (
    RankBM25CloudRetriever,
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


class FakeEncoder:
    def __init__(
        self,
        vector: models.SparseVector | None,
    ) -> None:
        self.vector = vector
        self.calls: list[str] = []

    def encode(
        self,
        query: str,
    ) -> models.SparseVector | None:
        self.calls.append(query)
        return self.vector


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


def _vector() -> models.SparseVector:
    return models.SparseVector(
        indices=[3, 7],
        values=[2.0, 1.5],
    )


def _retriever(
    client: FakeQdrantClient,
    *,
    encoder: FakeEncoder | None = None,
) -> RankBM25CloudRetriever:
    return RankBM25CloudRetriever(
        encoder=(
            encoder
            if encoder is not None
            else FakeEncoder(_vector())
        ),
        client=client,
        collection_name="cloud_collection",
        vector_name="rank_bm25_sparse",
    )


def test_module_import_does_not_load_rank_bm25() -> None:
    result = subprocess.run(
        [
            sys.executable,
            "-c",
            (
                "import sys; "
                "import backend.retrieval."
                "rank_bm25_cloud_retriever; "
                "print('rank_bm25' in sys.modules)"
            ),
        ],
        check=True,
        capture_output=True,
        text=True,
    )

    assert result.stdout.strip() == "False"


def test_retrieve_encodes_query_and_queries_sparse_vector() -> None:
    encoder = FakeEncoder(
        _vector()
    )
    client = FakeQdrantClient(
        [
            _point(
                chunk_id="chunk-1",
                document_id="doc-1",
                score=2.5,
            )
        ]
    )

    results = _retriever(
        client,
        encoder=encoder,
    ).retrieve(
        "What is Kubernetes?",
        top_k=1,
    )

    assert len(results) == 1
    assert encoder.calls == [
        "What is Kubernetes?"
    ]
    assert len(client.calls) == 1

    call = client.calls[0]

    assert call["collection_name"] == (
        "cloud_collection"
    )
    assert call["using"] == (
        "rank_bm25_sparse"
    )
    assert call["limit"] == 1
    assert call["with_payload"] is True

    query = call["query"]

    assert isinstance(
        query,
        models.SparseVector,
    )
    assert query.indices == [3, 7]
    assert query.values == pytest.approx(
        [2.0, 1.5]
    )


def test_retrieve_returns_empty_when_query_has_no_known_terms() -> None:
    encoder = FakeEncoder(None)
    client = FakeQdrantClient([])

    results = _retriever(
        client,
        encoder=encoder,
    ).retrieve(
        "unknown terms"
    )

    assert results == []
    assert encoder.calls == [
        "unknown terms"
    ]
    assert client.calls == []


def test_retrieve_maps_payload_to_result() -> None:
    client = FakeQdrantClient(
        [
            _point(
                chunk_id="chunk-1",
                document_id="doc-1",
                score=3.25,
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
        3.25
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


def test_retrieve_filters_non_positive_scores() -> None:
    client = FakeQdrantClient(
        [
            _point(
                chunk_id="positive",
                document_id="doc-1",
                score=1.0,
            ),
            _point(
                chunk_id="zero",
                document_id="doc-2",
                score=0.0,
            ),
            _point(
                chunk_id="negative",
                document_id="doc-3",
                score=-1.0,
            ),
        ]
    )

    results = _retriever(
        client
    ).retrieve(
        "query",
        top_k=3,
    )

    assert [
        result.chunk_id
        for result in results
    ] == ["positive"]


def test_retrieve_expands_candidate_pool_before_document_filtering() -> None:
    client = FakeQdrantClient(
        [
            _point(
                chunk_id="chunk-a1",
                document_id="doc-a",
                score=4.0,
            ),
            _point(
                chunk_id="chunk-a2",
                document_id="doc-a",
                score=3.0,
            ),
            _point(
                chunk_id="chunk-b1",
                document_id="doc-b",
                score=2.0,
            ),
            _point(
                chunk_id="chunk-c1",
                document_id="doc-c",
                score=1.0,
            ),
        ]
    )

    results = _retriever(
        client
    ).retrieve(
        "query",
        top_k=2,
        max_chunks_per_document=1,
        candidate_multiplier=5,
    )

    assert client.calls[0]["limit"] == 10
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
        ("   ", 5, None, 5),
        ("query", 0, None, 5),
        ("query", 5, 0, 5),
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
    ("collection", "vector"),
    [
        ("", "rank_bm25_sparse"),
        ("collection", ""),
    ],
)
def test_constructor_rejects_empty_configuration(
    collection: str,
    vector: str,
) -> None:
    with pytest.raises(ValueError):
        RankBM25CloudRetriever(
            encoder=FakeEncoder(
                _vector()
            ),
            client=FakeQdrantClient([]),
            collection_name=collection,
            vector_name=vector,
        )