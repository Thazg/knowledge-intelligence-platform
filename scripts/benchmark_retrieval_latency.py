from __future__ import annotations

import json
import statistics
import time
from dataclasses import asdict, dataclass
from pathlib import Path

from backend.chunking.serializer import ChunkSerializer
from backend.embedding.embedder import LocalEmbedder
from backend.evaluation.dataset_loader import (
    load_evaluation_cases,
)
from backend.query_rewriting.frozen_query_rewriter import (
    FrozenQueryRewriter,
)
from backend.reranking.cross_encoder_reranker import (
    CrossEncoderReranker,
)
from backend.retrieval.bm25_retriever import (
    BM25Retriever,
)
from backend.retrieval.dense_retriever import (
    DenseRetriever,
)
from backend.retrieval.hybrid_retriever import (
    HybridRetriever,
)
from backend.retrieval.multi_query_retriever import (
    MultiQueryRetriever,
)
from backend.retrieval.reranked_retriever import (
    RerankedRetriever,
)
from backend.vector_store.qdrant_store import (
    QdrantVectorStore,
)


PROJECT_ROOT = Path(__file__).resolve().parents[1]

DATASET_PATH = (
    PROJECT_ROOT
    / "benchmarks"
    / "retrieval"
    / "cases.jsonl"
)

CHUNKS_PATH = (
    PROJECT_ROOT
    / "data"
    / "processed"
    / "chunks_fixed.jsonl"
)

REWRITES_PATH = (
    PROJECT_ROOT
    / "benchmarks"
    / "retrieval"
    / "query_rewrites.jsonl"
)

REPORT_PATH = (
    PROJECT_ROOT
    / "benchmarks"
    / "retrieval"
    / "reports"
    / "retrieval_latency_v1.json"
)

COLLECTION_NAME = (
    "enterprise_knowledge_fixed_bge_small"
)

EMBEDDING_MODEL = (
    "BAAI/bge-small-en-v1.5"
)

RERANKER_MODEL = (
    "mixedbread-ai/mxbai-rerank-base-v2"
)

TOP_K = 10

WARMUP_QUERIES = 3


@dataclass(frozen=True)
class LatencyMetrics:
    runs: int
    mean_ms: float
    median_ms: float
    p50_ms: float
    p95_ms: float
    p99_ms: float
    min_ms: float
    max_ms: float


def percentile(
    values: list[float],
    percentile_value: float,
) -> float:
    if not values:
        return 0.0

    sorted_values = sorted(values)

    if len(sorted_values) == 1:
        return sorted_values[0]

    position = (
        percentile_value
        / 100.0
        * (len(sorted_values) - 1)
    )

    lower_index = int(position)
    upper_index = min(
        lower_index + 1,
        len(sorted_values) - 1,
    )

    fraction = (
        position - lower_index
    )

    lower_value = sorted_values[
        lower_index
    ]

    upper_value = sorted_values[
        upper_index
    ]

    return (
        lower_value
        + (
            upper_value
            - lower_value
        )
        * fraction
    )


def calculate_latency_metrics(
    latencies_ms: list[float],
) -> LatencyMetrics:
    if not latencies_ms:
        return LatencyMetrics(
            runs=0,
            mean_ms=0.0,
            median_ms=0.0,
            p50_ms=0.0,
            p95_ms=0.0,
            p99_ms=0.0,
            min_ms=0.0,
            max_ms=0.0,
        )

    return LatencyMetrics(
        runs=len(latencies_ms),
        mean_ms=statistics.mean(
            latencies_ms
        ),
        median_ms=statistics.median(
            latencies_ms
        ),
        p50_ms=percentile(
            latencies_ms,
            50,
        ),
        p95_ms=percentile(
            latencies_ms,
            95,
        ),
        p99_ms=percentile(
            latencies_ms,
            99,
        ),
        min_ms=min(
            latencies_ms
        ),
        max_ms=max(
            latencies_ms
        ),
    )


def benchmark_retriever(
    name: str,
    retriever,
    queries: list[str],
) -> LatencyMetrics:
    print()
    print("=" * 80)
    print(f"BENCHMARK: {name}")
    print("=" * 80)

    warmup_queries = queries[
        :WARMUP_QUERIES
    ]

    print(
        f"Warmup runs: "
        f"{len(warmup_queries)}"
    )

    for query in warmup_queries:
        retriever.retrieve(
            query=query,
            top_k=TOP_K,
            max_chunks_per_document=1,
        )

    print("Warmup complete.")
    print()

    latencies_ms: list[float] = []

    total_queries = len(queries)

    benchmark_start = (
        time.perf_counter()
    )

    for index, query in enumerate(
        queries,
        start=1,
    ):
        query_start = (
            time.perf_counter()
        )

        retriever.retrieve(
            query=query,
            top_k=TOP_K,
            max_chunks_per_document=1,
        )

        elapsed_ms = (
            time.perf_counter()
            - query_start
        ) * 1000.0

        latencies_ms.append(
            elapsed_ms
        )

        elapsed_total = (
            time.perf_counter()
            - benchmark_start
        )

        average_seconds = (
            elapsed_total / index
        )

        remaining = (
            total_queries - index
        )

        eta_seconds = (
            average_seconds
            * remaining
        )

        print(
            f"[{index:>3}/{total_queries}] "
            f"{elapsed_ms:>9.2f} ms | "
            f"ETA {eta_seconds / 60:.1f} min"
        )

    metrics = calculate_latency_metrics(
        latencies_ms
    )

    print()
    print(
        f"Mean   : "
        f"{metrics.mean_ms:.2f} ms"
    )
    print(
        f"Median : "
        f"{metrics.median_ms:.2f} ms"
    )
    print(
        f"P50    : "
        f"{metrics.p50_ms:.2f} ms"
    )
    print(
        f"P95    : "
        f"{metrics.p95_ms:.2f} ms"
    )
    print(
        f"P99    : "
        f"{metrics.p99_ms:.2f} ms"
    )
    print(
        f"Min    : "
        f"{metrics.min_ms:.2f} ms"
    )
    print(
        f"Max    : "
        f"{metrics.max_ms:.2f} ms"
    )

    return metrics


def main() -> None:
    cases = load_evaluation_cases(
        DATASET_PATH,
        active_only=True,
    )

    if not cases:
        raise ValueError(
            "No active evaluation cases found."
        )

    queries = [
        case.query
        for case in cases
    ]

    print(
        f"Loaded cases : {len(cases)}"
    )

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

    dense_retriever = DenseRetriever(
        embedder=embedder,
        vector_store=vector_store,
    )

    bm25_retriever = BM25Retriever(
        chunks=chunks,
    )

    weighted_rrf = HybridRetriever(
        dense_retriever=dense_retriever,
        bm25_retriever=bm25_retriever,
        rrf_k=60,
        dense_weight=0.7,
        bm25_weight=0.3,
    )

    frozen_rewriter = (
        FrozenQueryRewriter(
            rewrites_path=REWRITES_PATH,
        )
    )

    multi_query = MultiQueryRetriever(
        base_retriever=weighted_rrf,
        query_rewriter=frozen_rewriter,
        rrf_k=60,
        candidate_multiplier=5,
        query_weights=[
            1.0,
            0.7,
            0.7,
        ],
    )

    cross_encoder = (
        CrossEncoderReranker(
            model_name=RERANKER_MODEL,
            batch_size=16,
        )
    )

    reranked_hybrid = (
        RerankedRetriever(
            base_retriever=weighted_rrf,
            reranker=cross_encoder,
            candidate_multiplier=2,
        )
    )

    retrievers = {
        "dense": dense_retriever,
        "bm25": bm25_retriever,
        "weighted_rrf": weighted_rrf,
        "multi_query": multi_query,
        "reranked_hybrid": (
            reranked_hybrid
        ),
    }

    benchmark_results: dict[
        str,
        LatencyMetrics,
    ] = {}

    for name, retriever in (
        retrievers.items()
    ):
        metrics = benchmark_retriever(
            name=name,
            retriever=retriever,
            queries=queries,
        )

        benchmark_results[
            name
        ] = metrics

    REPORT_PATH.parent.mkdir(
        parents=True,
        exist_ok=True,
    )

    report = {
        "benchmark": {
            "name": (
                "retrieval_latency_v1"
            ),
            "cases": len(cases),
            "top_k": TOP_K,
            "warmup_queries": (
                WARMUP_QUERIES
            ),
        },
        "configuration": {
            "embedding_model": (
                EMBEDDING_MODEL
            ),
            "reranker_model": (
                RERANKER_MODEL
            ),
            "collection": (
                COLLECTION_NAME
            ),
            "weighted_rrf": {
                "dense_weight": 0.7,
                "bm25_weight": 0.3,
                "rrf_k": 60,
            },
            "multi_query": {
                "candidate_multiplier": 5,
                "query_weights": [
                    1.0,
                    0.7,
                    0.7,
                ],
            },
            "reranked_hybrid": {
                "candidate_multiplier": 2,
            },
        },
        "latency_ms": {
            name: asdict(metrics)
            for name, metrics
            in benchmark_results.items()
        },
    }

    with REPORT_PATH.open(
        "w",
        encoding="utf-8",
    ) as file:
        json.dump(
            report,
            file,
            indent=2,
            ensure_ascii=False,
        )

    print()
    print("=" * 80)
    print("LATENCY BENCHMARK COMPLETE")
    print("=" * 80)
    print(
        f"Report: {REPORT_PATH}"
    )


if __name__ == "__main__":
    main()