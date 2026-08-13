from __future__ import annotations

import hashlib
import json
import statistics
import time
from dataclasses import asdict, dataclass
from pathlib import Path

from backend.chunking.serializer import (
    ChunkSerializer,
)
from backend.embedding.embedder import (
    LocalEmbedder,
)
from backend.evaluation.dataset_loader import (
    load_evaluation_cases,
)
from backend.evaluation.metrics import (
    calculate_metrics,
    print_metrics,
)
from backend.evaluation.retrieval_evaluator import (
    EvaluationCase,
    EvaluationResult,
    RetrievalEvaluator,
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

GROUND_TRUTH_PATH = (
    PROJECT_ROOT
    / "benchmarks"
    / "retrieval"
    / "routing"
    / "ground_truth_v1.jsonl"
)

REWRITES_PATH = (
    PROJECT_ROOT
    / "benchmarks"
    / "retrieval"
    / "routing"
    / "query_rewrites_v1.jsonl"
)

CHUNKS_PATH = (
    PROJECT_ROOT
    / "data"
    / "processed"
    / "chunks_fixed.jsonl"
)

REPORT_PATH = (
    PROJECT_ROOT
    / "benchmarks"
    / "retrieval"
    / "routing"
    / "strategy_benchmark_v1.json"
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

GROUND_TRUTH_SHA256 = (
    "DF1D561F7E4F8D699770F219E7CA5E404AF98CA7704EDD7D53E6966183332341"
)

REWRITES_SHA256 = (
    "17AB187DF9761523773D62689FB45A19FCE600C7B2C587D40AE83C3B51F92010"
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


def sha256_file(
    path: Path,
) -> str:
    digest = hashlib.sha256()

    with path.open("rb") as file:
        while chunk := file.read(
            1024 * 1024
        ):
            digest.update(chunk)

    return digest.hexdigest().upper()


def validate_frozen_artifacts() -> None:
    ground_truth_hash = sha256_file(
        GROUND_TRUTH_PATH
    )

    rewrites_hash = sha256_file(
        REWRITES_PATH
    )

    if ground_truth_hash != GROUND_TRUTH_SHA256:
        raise ValueError(
            "Frozen ground truth hash mismatch. "
            f"Expected {GROUND_TRUTH_SHA256}, "
            f"received {ground_truth_hash}."
        )

    if rewrites_hash != REWRITES_SHA256:
        raise ValueError(
            "Frozen query rewrite hash mismatch. "
            f"Expected {REWRITES_SHA256}, "
            f"received {rewrites_hash}."
        )

    print("Frozen artifact validation: PASS")
    print(
        f"Ground truth SHA256: "
        f"{ground_truth_hash}"
    )
    print(
        f"Rewrites SHA256    : "
        f"{rewrites_hash}"
    )


def load_case_metadata() -> dict[str, dict]:
    metadata: dict[str, dict] = {}

    with GROUND_TRUTH_PATH.open(
        "r",
        encoding="utf-8",
    ) as file:
        for line in file:
            line = line.strip()

            if not line:
                continue

            record = json.loads(line)

            case_id = record["case_id"]

            if case_id in metadata:
                raise ValueError(
                    f"Duplicate case_id: {case_id}"
                )

            metadata[case_id] = {
                "initial_label": record.get(
                    "initial_label"
                ),
                "difficulty": record.get(
                    "difficulty"
                ),
                "technologies": record.get(
                    "technologies",
                    [],
                ),
            }

    return metadata


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
        min_ms=min(latencies_ms),
        max_ms=max(latencies_ms),
    )


def serialize_case_metrics(
    result: EvaluationResult,
    latency_ms: float,
) -> dict:
    return {
        "hit_at_1": float(
            result.hit_at_k(1)
        ),
        "hit_at_3": float(
            result.hit_at_k(3)
        ),
        "hit_at_5": float(
            result.hit_at_k(5)
        ),
        "hit_at_10": float(
            result.hit_at_k(10)
        ),
        "recall_at_3": (
            result.recall_at_k(3)
        ),
        "recall_at_5": (
            result.recall_at_k(5)
        ),
        "recall_at_10": (
            result.recall_at_k(10)
        ),
        "ndcg_at_3": (
            result.ndcg_at_k(3)
        ),
        "ndcg_at_5": (
            result.ndcg_at_k(5)
        ),
        "ndcg_at_10": (
            result.ndcg_at_k(10)
        ),
        "mrr": (
            result.reciprocal_rank
        ),
        "first_relevant_rank": (
            result.first_relevant_rank
        ),
        "latency_ms": latency_ms,
        "retrieved_relevant_documents": [
            {
                "source": document.source,
                "path": document.path,
                "rank": document.rank,
                "relevance": (
                    document.relevance
                ),
            }
            for document
            in result.retrieved_relevant_documents
        ],
    }


def evaluate_strategy(
    name: str,
    retriever,
    cases: list[EvaluationCase],
) -> tuple[
    list[EvaluationResult],
    list[float],
    dict[str, dict],
]:
    print()
    print("=" * 80)
    print(f"STRATEGY: {name}")
    print("=" * 80)

    warmup_cases = cases[
        :WARMUP_QUERIES
    ]

    print(
        f"Warmup runs: "
        f"{len(warmup_cases)}"
    )

    for case in warmup_cases:
        retriever.retrieve(
            query=case.query,
            top_k=TOP_K,
            max_chunks_per_document=1,
        )

    print("Warmup complete.")

    evaluator = RetrievalEvaluator(
        retriever=retriever,
    )

    results: list[
        EvaluationResult
    ] = []

    latencies_ms: list[float] = []

    per_case: dict[
        str,
        dict,
    ] = {}

    total_cases = len(cases)

    strategy_start = (
        time.perf_counter()
    )

    for index, case in enumerate(
        cases,
        start=1,
    ):
        query_start = (
            time.perf_counter()
        )

        result = evaluator.evaluate_case(
            case=case,
            top_k=TOP_K,
        )

        latency_ms = (
            time.perf_counter()
            - query_start
        ) * 1000.0

        results.append(result)

        latencies_ms.append(
            latency_ms
        )

        per_case[
            case.case_id
        ] = serialize_case_metrics(
            result=result,
            latency_ms=latency_ms,
        )

        elapsed = (
            time.perf_counter()
            - strategy_start
        )

        average_seconds = (
            elapsed / index
        )

        remaining = (
            total_cases - index
        )

        eta_seconds = (
            average_seconds
            * remaining
        )

        print(
            f"[{index:>2}/{total_cases}] "
            f"{case.case_id} | "
            f"{latency_ms:>9.2f} ms | "
            f"ETA {eta_seconds / 60:.1f} min"
        )

    return (
        results,
        latencies_ms,
        per_case,
    )


def main() -> None:
    validate_frozen_artifacts()

    cases = load_evaluation_cases(
        GROUND_TRUTH_PATH,
        active_only=False,
    )

    if len(cases) != 45:
        raise ValueError(
            "Expected exactly 45 routing "
            f"cases, found {len(cases)}."
        )

    metadata = load_case_metadata()

    if set(metadata) != {
        case.case_id
        for case in cases
    }:
        raise ValueError(
            "Ground-truth metadata and "
            "evaluation cases do not match."
        )

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

    frozen_rewriter = FrozenQueryRewriter(
        rewrites_path=REWRITES_PATH,
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

    reranker = CrossEncoderReranker(
        model_name=RERANKER_MODEL,
        batch_size=16,
    )

    reranked_hybrid = RerankedRetriever(
        base_retriever=weighted_rrf,
        reranker=reranker,
        candidate_multiplier=2,
    )

    strategies = {
        "standard": weighted_rrf,
        "coverage": multi_query,
        "high_quality": reranked_hybrid,
    }

    strategy_report: dict[
        str,
        dict,
    ] = {}

    case_report: dict[
        str,
        dict,
    ] = {
        case.case_id: {
            "case_id": case.case_id,
            "query": case.query,
            **metadata[case.case_id],
            "strategies": {},
        }
        for case in cases
    }

    for name, retriever in (
        strategies.items()
    ):
        (
            results,
            latencies_ms,
            per_case,
        ) = evaluate_strategy(
            name=name,
            retriever=retriever,
            cases=cases,
        )

        quality_metrics = (
            calculate_metrics(
                results
            )
        )

        latency_metrics = (
            calculate_latency_metrics(
                latencies_ms
            )
        )

        print_metrics(
            f"ROUTING STRATEGY: "
            f"{name.upper()}",
            quality_metrics,
        )

        print()
        print(
            "Latency mean : "
            f"{latency_metrics.mean_ms:.2f} ms"
        )
        print(
            "Latency p95  : "
            f"{latency_metrics.p95_ms:.2f} ms"
        )

        strategy_report[name] = {
            "quality": asdict(
                quality_metrics
            ),
            "latency_ms": asdict(
                latency_metrics
            ),
        }

        for case_id, metrics in (
            per_case.items()
        ):
            case_report[
                case_id
            ][
                "strategies"
            ][name] = metrics

    report = {
        "benchmark": {
            "name": (
                "routing_strategy_benchmark_v1"
            ),
            "cases": len(cases),
            "top_k": TOP_K,
            "warmup_queries": (
                WARMUP_QUERIES
            ),
        },
        "frozen_artifacts": {
            "ground_truth": {
                "path": str(
                    GROUND_TRUTH_PATH.relative_to(
                        PROJECT_ROOT
                    )
                ),
                "sha256": (
                    GROUND_TRUTH_SHA256
                ),
            },
            "query_rewrites": {
                "path": str(
                    REWRITES_PATH.relative_to(
                        PROJECT_ROOT
                    )
                ),
                "sha256": (
                    REWRITES_SHA256
                ),
            },
        },
        "configuration": {
            "collection": (
                COLLECTION_NAME
            ),
            "embedding_model": (
                EMBEDDING_MODEL
            ),
            "top_k": TOP_K,
            "standard": {
                "type": "weighted_rrf",
                "dense_weight": 0.7,
                "bm25_weight": 0.3,
                "rrf_k": 60,
            },
            "coverage": {
                "type": "multi_query",
                "base": "weighted_rrf",
                "rrf_k": 60,
                "candidate_multiplier": 5,
                "query_weights": [
                    1.0,
                    0.7,
                    0.7,
                ],
                "queries_per_case": 3,
            },
            "high_quality": {
                "type": (
                    "reranked_weighted_rrf"
                ),
                "reranker_model": (
                    RERANKER_MODEL
                ),
                "reranker_batch_size": 16,
                "candidate_multiplier": 2,
                "candidate_pool": (
                    TOP_K * 2
                ),
            },
            "latency": {
                "timer": (
                    "time.perf_counter"
                ),
                "warmup_queries": (
                    WARMUP_QUERIES
                ),
                "model_initialization_included": (
                    False
                ),
                "retrieval_runs_per_case": 1,
            },
        },
        "strategies": strategy_report,
        "cases": [
            case_report[
                case.case_id
            ]
            for case in cases
        ],
    }

    REPORT_PATH.parent.mkdir(
        parents=True,
        exist_ok=True,
    )

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
    print(
        "ROUTING STRATEGY BENCHMARK COMPLETE"
    )
    print("=" * 80)
    print(
        f"Report: {REPORT_PATH}"
    )


if __name__ == "__main__":
    main()