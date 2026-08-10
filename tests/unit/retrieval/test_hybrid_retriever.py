from __future__ import annotations

from typing import Any

import pytest

from backend.retrieval.hybrid_retriever import HybridRetriever
from backend.retrieval.models import RetrievalResult


class StubRetriever:
    def __init__(self, results: list[RetrievalResult]) -> None:
        self.results = results
        self.calls: list[dict[str, Any]] = []

    def retrieve(
        self,
        query: str,
        top_k: int,
        max_chunks_per_document: int | None,
    ) -> list[RetrievalResult]:
        self.calls.append(
            {
                "query": query,
                "top_k": top_k,
                "max_chunks_per_document": max_chunks_per_document,
            }
        )
        return self.results[:top_k]


def make_result(
    chunk_id: str,
    rank: int,
    *,
    document_id: str | None = None,
    source: str = "synthetic",
    content: str | None = None,
    title: str | None = None,
) -> RetrievalResult:
    return RetrievalResult(
        chunk_id=chunk_id,
        document_id=document_id or f"document-{chunk_id}",
        content=content or f"Content for {chunk_id}",
        score=100.0 - rank,
        rank=rank,
        source=source,
        filename=f"{chunk_id}.md",
        relative_path=f"{source}/{chunk_id}.md",
        chunk_index=rank - 1,
        token_count=10 + rank,
        title=title,
    )


def build_hybrid(
    dense_results: list[RetrievalResult],
    bm25_results: list[RetrievalResult],
    **configuration: Any,
) -> tuple[HybridRetriever, StubRetriever, StubRetriever]:
    dense = StubRetriever(dense_results)
    bm25 = StubRetriever(bm25_results)
    hybrid = HybridRetriever(
        dense_retriever=dense,
        bm25_retriever=bm25,
        **configuration,
    )
    return hybrid, dense, bm25


def test_weighted_rrf_fuses_overlap_and_unique_results() -> None:
    hybrid, _, _ = build_hybrid(
        dense_results=[
            make_result("A", 1, source="dense"),
            make_result(
                "B",
                2,
                source="dense",
                content="Dense content for B",
                title="Dense title for B",
            ),
            make_result("C", 3, source="dense"),
        ],
        bm25_results=[
            make_result(
                "B",
                1,
                source="bm25",
                content="BM25 content for B",
                title="BM25 title for B",
            ),
            make_result("D", 2, source="bm25"),
            make_result("A", 3, source="bm25"),
        ],
        rrf_k=60,
        dense_weight=0.7,
        bm25_weight=0.3,
    )

    results = hybrid.retrieve(
        query="synthetic query",
        top_k=4,
        max_chunks_per_document=None,
    )

    assert [result.chunk_id for result in results] == ["A", "B", "C", "D"]
    assert [result.score for result in results] == [
        0.7 / (60 + 1) + 0.3 / (60 + 3),
        0.7 / (60 + 2) + 0.3 / (60 + 1),
        0.7 / (60 + 3),
        0.3 / (60 + 2),
    ]
    assert [result.rank for result in results] == [1, 2, 3, 4]
    assert [result.score for result in results] == sorted(
        (result.score for result in results),
        reverse=True,
    )

    overlapping_result = results[1]
    assert overlapping_result.content == "Dense content for B"
    assert overlapping_result.source == "dense"
    assert overlapping_result.title == "Dense title for B"

    bm25_only_result = results[3]
    assert bm25_only_result.content == "Content for D"
    assert bm25_only_result.source == "bm25"


def test_equal_scores_keep_dense_then_bm25_insertion_order() -> None:
    hybrid, _, _ = build_hybrid(
        dense_results=[make_result("dense-only", 1)],
        bm25_results=[make_result("bm25-only", 1)],
        rrf_k=10,
        dense_weight=1.0,
        bm25_weight=1.0,
    )

    results = hybrid.retrieve(
        query="tie query",
        top_k=2,
        max_chunks_per_document=None,
    )

    assert [result.score for result in results] == [1.0 / 11, 1.0 / 11]
    assert [result.chunk_id for result in results] == [
        "dense-only",
        "bm25-only",
    ]


def test_document_limit_is_applied_after_fusion() -> None:
    hybrid, _, _ = build_hybrid(
        dense_results=[
            make_result("A", 1, document_id="shared-document"),
            make_result("B", 2, document_id="shared-document"),
            make_result("C", 3, document_id="other-document"),
        ],
        bm25_results=[],
    )

    results = hybrid.retrieve(
        query="document filtering",
        top_k=2,
        max_chunks_per_document=1,
    )

    assert [result.chunk_id for result in results] == ["A", "C"]
    assert [result.rank for result in results] == [1, 2]


def test_top_k_truncates_and_expands_upstream_candidate_pool() -> None:
    hybrid, dense, bm25 = build_hybrid(
        dense_results=[
            make_result("A", 1),
            make_result("B", 2),
            make_result("C", 3),
        ],
        bm25_results=[make_result("D", 1)],
    )

    results = hybrid.retrieve(
        query="candidate expansion",
        top_k=2,
        max_chunks_per_document=None,
        candidate_multiplier=3,
    )

    expected_call = {
        "query": "candidate expansion",
        "top_k": 6,
        "max_chunks_per_document": None,
    }
    assert dense.calls == [expected_call]
    assert bm25.calls == [expected_call]
    assert len(results) == 2
    assert [result.rank for result in results] == [1, 2]


@pytest.mark.parametrize(
    "configuration",
    [
        {"rrf_k": 0},
        {"dense_weight": -0.1},
        {"bm25_weight": -0.1},
        {"dense_weight": 0.0, "bm25_weight": 0.0},
    ],
)
def test_invalid_configuration_is_rejected(
    configuration: dict[str, Any],
) -> None:
    with pytest.raises(ValueError):
        build_hybrid([], [], **configuration)


@pytest.mark.parametrize(
    "arguments",
    [
        {"query": ""},
        {"query": "   "},
        {"query": "query", "top_k": 0},
        {"query": "query", "max_chunks_per_document": 0},
        {"query": "query", "candidate_multiplier": 0},
    ],
)
def test_invalid_retrieval_arguments_are_rejected_before_source_calls(
    arguments: dict[str, Any],
) -> None:
    hybrid, dense, bm25 = build_hybrid([], [])

    with pytest.raises(ValueError):
        hybrid.retrieve(**arguments)

    assert dense.calls == []
    assert bm25.calls == []
