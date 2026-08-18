from __future__ import annotations

import argparse
import json
import os
import time
from collections import Counter
from pathlib import Path
from typing import Any
from uuid import NAMESPACE_URL, uuid5

from qdrant_client import QdrantClient, models

from backend.chunking.serializer import ChunkSerializer
from backend.evaluation.dataset_loader import (
    load_evaluation_cases,
)
from backend.retrieval.bm25_retriever import BM25Retriever


PROJECT_ROOT = Path(__file__).resolve().parents[1]

CHUNKS_PATH = (
    PROJECT_ROOT
    / "data"
    / "processed"
    / "chunks_fixed.jsonl"
)

CASES_PATH = (
    PROJECT_ROOT
    / "benchmarks"
    / "retrieval"
    / "cases.jsonl"
)

DEFAULT_COLLECTION = (
    "enterprise_knowledge_rank_bm25_parity_canary"
)

DEFAULT_OUTPUT = (
    PROJECT_ROOT
    / ".benchmark-results"
    / "rank-bm25-qdrant-parity-canary.json"
)

SPARSE_VECTOR_NAME = "rank_bm25_sparse"

DEFAULT_SAMPLE_SIZE = 500
DEFAULT_TOP_K = 10
DEFAULT_QUERY_COUNT = 100


def _require_env(name: str) -> str:
    value = os.getenv(name, "").strip()

    if not value:
        raise RuntimeError(
            f"{name} is required. "
            "Set it in the current shell before running."
        )

    return value


def _select_evenly_spaced(
    items: list[Any],
    limit: int,
) -> list[Any]:
    if limit >= len(items):
        return list(items)

    if limit == 1:
        return [items[0]]

    max_index = len(items) - 1

    indexes = [
        round(
            position
            * max_index
            / (limit - 1)
        )
        for position in range(limit)
    ]

    return [
        items[index]
        for index in indexes
    ]


def _point_id(chunk_id: str) -> str:
    return str(
        uuid5(
            NAMESPACE_URL,
            f"enterprise-kip:rank-bm25:{chunk_id}",
        )
    )


def _build_vocabulary(
    bm25: BM25Retriever,
) -> dict[str, int]:
    terms = sorted(
        {
            term
            for doc_freq
            in bm25.index.doc_freqs
            for term in doc_freq
        }
    )

    # Start at 1 simply to keep 0 unused.
    return {
        term: index
        for index, term in enumerate(
            terms,
            start=1,
        )
    }


def _encode_document(
    *,
    bm25: BM25Retriever,
    doc_position: int,
    vocabulary: dict[str, int],
) -> models.SparseVector:
    index = bm25.index

    frequencies = index.doc_freqs[
        doc_position
    ]

    doc_length = index.doc_len[
        doc_position
    ]

    normalization = (
        index.k1
        * (
            1
            - index.b
            + (
                index.b
                * doc_length
                / index.avgdl
            )
        )
    )

    entries: list[
        tuple[int, float]
    ] = []

    for term, frequency in (
        frequencies.items()
    ):
        value = (
            frequency
            * (index.k1 + 1)
            / (
                frequency
                + normalization
            )
        )

        if value == 0:
            continue

        entries.append(
            (
                vocabulary[term],
                float(value),
            )
        )

    entries.sort(
        key=lambda item: item[0]
    )

    return models.SparseVector(
        indices=[
            index
            for index, _ in entries
        ],
        values=[
            value
            for _, value in entries
        ],
    )


def _encode_query(
    *,
    bm25: BM25Retriever,
    query: str,
    vocabulary: dict[str, int],
) -> models.SparseVector | None:
    tokens = bm25._tokenize(query)

    if not tokens:
        return None

    token_counts = Counter(tokens)

    entries: list[
        tuple[int, float]
    ] = []

    for term, query_frequency in (
        token_counts.items()
    ):
        sparse_index = vocabulary.get(
            term
        )

        if sparse_index is None:
            continue

        idf = float(
            bm25.index.idf.get(
                term,
                0.0,
            )
        )

        value = (
            idf
            * query_frequency
        )

        if value == 0:
            continue

        entries.append(
            (
                sparse_index,
                value,
            )
        )

    if not entries:
        return None

    entries.sort(
        key=lambda item: item[0]
    )

    return models.SparseVector(
        indices=[
            index
            for index, _ in entries
        ],
        values=[
            value
            for _, value in entries
        ],
    )


def _build_points(
    *,
    bm25: BM25Retriever,
    chunks: list[Any],
    vocabulary: dict[str, int],
) -> list[models.PointStruct]:
    points = []

    for position, chunk in enumerate(
        chunks
    ):
        points.append(
            models.PointStruct(
                id=_point_id(
                    chunk.chunk_id
                ),
                vector={
                    SPARSE_VECTOR_NAME: (
                        _encode_document(
                            bm25=bm25,
                            doc_position=position,
                            vocabulary=vocabulary,
                        )
                    )
                },
                payload={
                    "chunk_id": chunk.chunk_id,
                    "document_id": (
                        chunk.document_id
                    ),
                    "source": chunk.source,
                    "relative_path": (
                        chunk.relative_path
                    ),
                    "title": chunk.title,
                },
            )
        )

    return points


def _create_collection(
    client: QdrantClient,
    *,
    collection_name: str,
    recreate: bool,
) -> None:
    exists = client.collection_exists(
        collection_name
    )

    if exists and not recreate:
        raise RuntimeError(
            f"Collection {collection_name!r} "
            "already exists. Use --recreate "
            "only for this parity canary."
        )

    if exists:
        print(
            "Deleting existing parity "
            "collection..."
        )

        client.delete_collection(
            collection_name
        )

    print(
        "Creating parity collection..."
    )

    client.create_collection(
        collection_name=collection_name,
        vectors_config={},
        sparse_vectors_config={
            SPARSE_VECTOR_NAME: (
                models.SparseVectorParams(
                    index=(
                        models.SparseIndexParams()
                    )
                )
            )
        },
    )


def _local_results(
    *,
    bm25: BM25Retriever,
    query: str,
    top_k: int,
) -> list[dict[str, Any]]:
    results = bm25.retrieve(
        query=query,
        top_k=top_k,
        max_chunks_per_document=None,
    )

    return [
        {
            "chunk_id": result.chunk_id,
            "score": float(result.score),
            "rank": result.rank,
        }
        for result in results
    ]


def _qdrant_results(
    *,
    client: QdrantClient,
    collection_name: str,
    query_vector: (
        models.SparseVector | None
    ),
    top_k: int,
) -> list[dict[str, Any]]:
    if query_vector is None:
        return []

    response = client.query_points(
        collection_name=collection_name,
        query=query_vector,
        using=SPARSE_VECTOR_NAME,
        limit=top_k,
        with_payload=True,
    )

    results = []

    for point in response.points:
        score = float(point.score)

        # Match BM25Retriever's score <= 0 filter.
        if score <= 0:
            continue

        payload = point.payload or {}

        results.append(
            {
                "chunk_id": str(
                    payload.get(
                        "chunk_id",
                        "",
                    )
                ),
                "score": score,
                "rank": len(results) + 1,
            }
        )

    return results


def _compare_results(
    local: list[dict[str, Any]],
    remote: list[dict[str, Any]],
) -> dict[str, Any]:
    local_ids = [
        item["chunk_id"]
        for item in local
    ]

    remote_ids = [
        item["chunk_id"]
        for item in remote
    ]

    exact_order = (
        local_ids == remote_ids
    )

    if not local_ids and not remote_ids:
        overlap = 1.0
    elif not local_ids:
        overlap = 0.0
    else:
        overlap = (
            len(
                set(local_ids)
                & set(remote_ids)
            )
            / len(set(local_ids))
        )

    local_scores = {
        item["chunk_id"]: item["score"]
        for item in local
    }

    remote_scores = {
        item["chunk_id"]: item["score"]
        for item in remote
    }

    shared_ids = (
        set(local_scores)
        & set(remote_scores)
    )

    score_deltas = [
        abs(
            local_scores[chunk_id]
            - remote_scores[chunk_id]
        )
        for chunk_id in shared_ids
    ]

    max_score_delta = (
        max(score_deltas)
        if score_deltas
        else 0.0
    )

    return {
        "exact_order": exact_order,
        "local_count": len(local_ids),
        "remote_count": len(remote_ids),
        "overlap": overlap,
        "max_score_delta": (
            max_score_delta
        ),
        "local_ids": local_ids,
        "remote_ids": remote_ids,
    }


def _parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description=(
            "Check whether explicit Qdrant "
            "sparse vectors reproduce the "
            "existing rank_bm25 BM25Okapi "
            "ranking and scores."
        )
    )

    parser.add_argument(
        "--sample-size",
        type=int,
        default=DEFAULT_SAMPLE_SIZE,
    )

    parser.add_argument(
        "--query-count",
        type=int,
        default=DEFAULT_QUERY_COUNT,
    )

    parser.add_argument(
        "--top-k",
        type=int,
        default=DEFAULT_TOP_K,
    )

    parser.add_argument(
        "--collection",
        default=DEFAULT_COLLECTION,
    )

    parser.add_argument(
        "--batch-size",
        type=int,
        default=64,
    )

    parser.add_argument(
        "--output",
        type=Path,
        default=DEFAULT_OUTPUT,
    )

    parser.add_argument(
        "--recreate",
        action="store_true",
    )

    args = parser.parse_args()

    if args.sample_size < 1:
        parser.error(
            "--sample-size must be >= 1"
        )

    if args.query_count < 1:
        parser.error(
            "--query-count must be >= 1"
        )

    if args.top_k < 1:
        parser.error(
            "--top-k must be >= 1"
        )

    if args.batch_size < 1:
        parser.error(
            "--batch-size must be >= 1"
        )

    return args


def main() -> None:
    args = _parse_args()

    qdrant_url = _require_env(
        "QDRANT_URL"
    )

    qdrant_api_key = _require_env(
        "QDRANT_API_KEY"
    )

    serializer = ChunkSerializer()

    all_chunks = serializer.load_jsonl(
        CHUNKS_PATH
    )

    sample_size = min(
        args.sample_size,
        len(all_chunks),
    )

    chunks = _select_evenly_spaced(
        all_chunks,
        sample_size,
    )

    cases = load_evaluation_cases(
        CASES_PATH
    )

    query_count = min(
        args.query_count,
        len(cases),
    )

    cases = cases[:query_count]

    print(
        "RANK_BM25 → QDRANT SPARSE "
        "PARITY CANARY"
    )
    print(
        "================================"
    )
    print(
        f"Corpus chunks: "
        f"{len(all_chunks):,}"
    )
    print(
        f"Canary chunks: "
        f"{len(chunks):,}"
    )
    print(
        f"Queries: {len(cases)}"
    )
    print(
        f"Top K: {args.top_k}"
    )
    print()

    print(
        "Building canonical BM25Okapi "
        "over canary chunks..."
    )

    bm25 = BM25Retriever(
        chunks=chunks
    )

    vocabulary = _build_vocabulary(
        bm25
    )

    print(
        f"Vocabulary size: "
        f"{len(vocabulary):,}"
    )
    print(
        f"BM25 k1: {bm25.index.k1}"
    )
    print(
        f"BM25 b: {bm25.index.b}"
    )
    print(
        f"BM25 epsilon: "
        f"{bm25.index.epsilon}"
    )
    print(
        f"BM25 avgdl: "
        f"{bm25.index.avgdl:.4f}"
    )
    print()

    client = QdrantClient(
        url=qdrant_url,
        api_key=qdrant_api_key,
        timeout=120.0,
    )

    _create_collection(
        client,
        collection_name=args.collection,
        recreate=args.recreate,
    )

    print(
        "Encoding explicit sparse "
        "document vectors..."
    )

    points = _build_points(
        bm25=bm25,
        chunks=chunks,
        vocabulary=vocabulary,
    )

    print(
        "Uploading parity points..."
    )

    client.upload_points(
        collection_name=args.collection,
        points=points,
        batch_size=args.batch_size,
        parallel=1,
        max_retries=3,
        wait=True,
    )

    actual_count = int(
        client.count(
            collection_name=args.collection,
            exact=True,
        ).count
    )

    print(
        f"Exact collection points: "
        f"{actual_count:,}"
    )

    if actual_count != len(chunks):
        raise RuntimeError(
            "Parity collection count "
            "mismatch."
        )

    print()
    print(
        "Comparing local BM25 with "
        "Qdrant sparse..."
    )
    print()

    comparisons = []

    started_at = time.perf_counter()

    for position, case in enumerate(
        cases,
        start=1,
    ):
        local = _local_results(
            bm25=bm25,
            query=case.query,
            top_k=args.top_k,
        )

        query_vector = _encode_query(
            bm25=bm25,
            query=case.query,
            vocabulary=vocabulary,
        )

        remote = _qdrant_results(
            client=client,
            collection_name=args.collection,
            query_vector=query_vector,
            top_k=args.top_k,
        )

        comparison = _compare_results(
            local,
            remote,
        )

        comparison["case_id"] = (
            case.case_id
        )
        comparison["query"] = case.query

        comparisons.append(
            comparison
        )

        print(
            f"[{position:03d}/{len(cases):03d}] "
            f"{case.case_id} "
            f"exact="
            f"{comparison['exact_order']} "
            f"overlap="
            f"{comparison['overlap']:.3f} "
            f"max_score_delta="
            f"{comparison['max_score_delta']:.8f}"
        )

    elapsed_seconds = (
        time.perf_counter()
        - started_at
    )

    exact_count = sum(
        item["exact_order"]
        for item in comparisons
    )

    exact_rate = (
        exact_count
        / len(comparisons)
    )

    mean_overlap = (
        sum(
            item["overlap"]
            for item in comparisons
        )
        / len(comparisons)
    )

    max_score_delta = max(
        item["max_score_delta"]
        for item in comparisons
    )

    mismatches = [
        item
        for item in comparisons
        if not item["exact_order"]
    ]

    print()
    print(
        "PARITY SUMMARY"
    )
    print(
        "=============="
    )
    print(
        f"Queries: {len(comparisons)}"
    )
    print(
        f"Exact top-{args.top_k} "
        f"order: "
        f"{exact_count}/{len(comparisons)} "
        f"({exact_rate * 100:.2f}%)"
    )
    print(
        f"Mean top-{args.top_k} "
        f"local coverage: "
        f"{mean_overlap:.6f}"
    )
    print(
        "Maximum shared-result "
        "score delta: "
        f"{max_score_delta:.10f}"
    )
    print(
        f"Mismatched queries: "
        f"{len(mismatches)}"
    )
    print(
        f"Comparison runtime: "
        f"{elapsed_seconds:.2f}s"
    )

    if mismatches:
        print()
        print(
            "FIRST MISMATCHES"
        )
        print(
            "================"
        )

        for item in mismatches[:5]:
            print(
                f"{item['case_id']}: "
                f"{item['query']}"
            )
            print(
                "  local : "
                f"{item['local_ids']}"
            )
            print(
                "  qdrant: "
                f"{item['remote_ids']}"
            )

    report = {
        "status": (
            "pass"
            if exact_rate >= 0.99
            and mean_overlap >= 0.99
            else "review"
        ),
        "sample": {
            "corpus_chunks": (
                len(all_chunks)
            ),
            "canary_chunks": len(chunks),
            "selection": (
                "evenly_spaced"
            ),
        },
        "bm25": {
            "k1": bm25.index.k1,
            "b": bm25.index.b,
            "epsilon": (
                bm25.index.epsilon
            ),
            "avgdl": bm25.index.avgdl,
            "vocabulary_size": (
                len(vocabulary)
            ),
        },
        "queries": len(cases),
        "top_k": args.top_k,
        "parity": {
            "exact_order_count": (
                exact_count
            ),
            "exact_order_rate": (
                exact_rate
            ),
            "mean_local_coverage": (
                mean_overlap
            ),
            "max_score_delta": (
                max_score_delta
            ),
            "mismatch_count": (
                len(mismatches)
            ),
        },
        "comparisons": comparisons,
    }

    args.output.parent.mkdir(
        parents=True,
        exist_ok=True,
    )

    args.output.write_text(
        json.dumps(
            report,
            indent=2,
            ensure_ascii=False,
        )
        + "\n",
        encoding="utf-8",
    )

    print()
    print(
        f"Report written to: "
        f"{args.output}"
    )
    print()
    print(
        "Canary complete. "
        "Do not build the full sparse "
        "corpus until parity is reviewed."
    )


if __name__ == "__main__":
    main()