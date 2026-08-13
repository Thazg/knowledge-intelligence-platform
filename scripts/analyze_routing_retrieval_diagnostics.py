from __future__ import annotations

import json
from collections import defaultdict
from pathlib import Path

from backend.chunking.serializer import (
    ChunkSerializer,
)
from backend.embedding.embedder import (
    LocalEmbedder,
)
from backend.retrieval.bm25_retriever import (
    BM25Retriever,
)
from backend.retrieval.dense_retriever import (
    DenseRetriever,
)
from backend.vector_store.qdrant_store import (
    QdrantVectorStore,
)


PROJECT_ROOT = Path(__file__).resolve().parents[1]

LABELS_PATH = (
    PROJECT_ROOT
    / "benchmarks"
    / "retrieval"
    / "routing"
    / "preferred_strategy_v1.jsonl"
)

CHUNKS_PATH = (
    PROJECT_ROOT
    / "data"
    / "processed"
    / "chunks_fixed.jsonl"
)

COLLECTION_NAME = (
    "enterprise_knowledge_fixed_bge_small"
)

EMBEDDING_MODEL = (
    "BAAI/bge-small-en-v1.5"
)

RETRIEVAL_K = 50


def load_labels() -> list[dict]:
    return [
        json.loads(line)
        for line in LABELS_PATH.read_text(
            encoding="utf-8"
        ).splitlines()
        if line.strip()
    ]


def document_key(result) -> tuple[str, str]:
    return (
        result.source.casefold(),
        result.relative_path
        .replace("\\", "/")
        .casefold(),
    )


def unique_documents(
    results,
    limit: int,
) -> list[tuple[str, str]]:
    documents: list[
        tuple[str, str]
    ] = []

    seen = set()

    for result in results:
        key = document_key(result)

        if key in seen:
            continue

        seen.add(key)
        documents.append(key)

        if len(documents) >= limit:
            break

    return documents


def overlap_at_k(
    dense_docs,
    bm25_docs,
    k: int,
) -> int:
    return len(
        set(dense_docs[:k])
        & set(bm25_docs[:k])
    )


def jaccard_at_k(
    dense_docs,
    bm25_docs,
    k: int,
) -> float:
    dense_set = set(
        dense_docs[:k]
    )

    bm25_set = set(
        bm25_docs[:k]
    )

    union = dense_set | bm25_set

    if not union:
        return 0.0

    return (
        len(dense_set & bm25_set)
        / len(union)
    )


def rank_of(
    target,
    documents,
) -> int | None:
    try:
        return (
            documents.index(target)
            + 1
        )
    except ValueError:
        return None


def mean(
    values: list[float],
) -> float:
    if not values:
        return 0.0

    return sum(values) / len(values)


def main() -> None:
    labels = load_labels()

    assert len(labels) == 45

    serializer = ChunkSerializer()

    chunks = serializer.load_jsonl(
        CHUNKS_PATH
    )

    print(
        f"Loaded chunks: {len(chunks):,}"
    )

    embedder = LocalEmbedder(
        model_name=EMBEDDING_MODEL,
    )

    vector_store = QdrantVectorStore(
        collection_name=COLLECTION_NAME,
        vector_size=embedder.dimension,
    )

    dense = DenseRetriever(
        embedder=embedder,
        vector_store=vector_store,
    )

    bm25 = BM25Retriever(
        chunks=chunks,
    )

    rows: list[dict] = []

    for index, label in enumerate(
        labels,
        start=1,
    ):
        query = label["query"]

        dense_results = dense.retrieve(
            query=query,
            top_k=RETRIEVAL_K,
            max_chunks_per_document=None,
        )

        bm25_results = bm25.retrieve(
            query=query,
            top_k=RETRIEVAL_K,
            max_chunks_per_document=None,
        )

        dense_docs = unique_documents(
            dense_results,
            RETRIEVAL_K,
        )

        bm25_docs = unique_documents(
            bm25_results,
            RETRIEVAL_K,
        )

        dense_top1 = (
            dense_docs[0]
            if dense_docs
            else None
        )

        bm25_top1 = (
            bm25_docs[0]
            if bm25_docs
            else None
        )

        row = {
            "case_id": (
                label["case_id"]
            ),
            "preferred_strategy": (
                label[
                    "preferred_strategy"
                ]
            ),
            "top1_agreement": (
                dense_top1 is not None
                and dense_top1
                == bm25_top1
            ),
            "overlap_at_3": (
                overlap_at_k(
                    dense_docs,
                    bm25_docs,
                    3,
                )
            ),
            "overlap_at_5": (
                overlap_at_k(
                    dense_docs,
                    bm25_docs,
                    5,
                )
            ),
            "overlap_at_10": (
                overlap_at_k(
                    dense_docs,
                    bm25_docs,
                    10,
                )
            ),
            "jaccard_at_5": (
                jaccard_at_k(
                    dense_docs,
                    bm25_docs,
                    5,
                )
            ),
            "jaccard_at_10": (
                jaccard_at_k(
                    dense_docs,
                    bm25_docs,
                    10,
                )
            ),
            "dense_top1_rank_in_bm25": (
                rank_of(
                    dense_top1,
                    bm25_docs,
                )
                if dense_top1
                else None
            ),
            "bm25_top1_rank_in_dense": (
                rank_of(
                    bm25_top1,
                    dense_docs,
                )
                if bm25_top1
                else None
            ),
        }

        rows.append(row)

        print(
            f"[{index:>2}/45] "
            f"{row['case_id']} | "
            f"{row['preferred_strategy']:<12} | "
            f"top1={row['top1_agreement']} | "
            f"O5={row['overlap_at_5']} | "
            f"O10={row['overlap_at_10']}"
        )

    grouped = defaultdict(list)

    for row in rows:
        strategy = row[
            "preferred_strategy"
        ]

        if strategy in {
            "standard",
            "high_quality",
        }:
            grouped[strategy].append(
                row
            )

    print()
    print("=" * 88)
    print(
        "DENSE / BM25 DIAGNOSTIC SUMMARY"
    )
    print("=" * 88)

    for strategy in (
        "standard",
        "high_quality",
    ):
        subset = grouped[strategy]

        print()
        print(
            f"{strategy.upper()} "
            f"({len(subset)} cases)"
        )
        print("-" * 88)

        top1_rate = mean([
            float(
                row[
                    "top1_agreement"
                ]
            )
            for row in subset
        ])

        print(
            f"Top1 agreement : "
            f"{top1_rate:.3f}"
        )

        for field in (
            "overlap_at_3",
            "overlap_at_5",
            "overlap_at_10",
            "jaccard_at_5",
            "jaccard_at_10",
        ):
            value = mean([
                float(row[field])
                for row in subset
            ])

            print(
                f"{field:<15}: "
                f"{value:.3f}"
            )

    print()
    print("=" * 88)
    print(
        "HIGH-QUALITY CASE DETAILS"
    )
    print("=" * 88)

    for row in rows:
        if (
            row["preferred_strategy"]
            != "high_quality"
        ):
            continue

        print(
            f"{row['case_id']} | "
            f"top1={row['top1_agreement']} | "
            f"O3={row['overlap_at_3']} | "
            f"O5={row['overlap_at_5']} | "
            f"O10={row['overlap_at_10']} | "
            f"J10={row['jaccard_at_10']:.3f} | "
            f"D1→B={row['dense_top1_rank_in_bm25']} | "
            f"B1→D={row['bm25_top1_rank_in_dense']}"
        )


if __name__ == "__main__":
    main()