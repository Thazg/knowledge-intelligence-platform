from __future__ import annotations

import json
import sys
from pathlib import Path

from backend.chunking.serializer import ChunkSerializer
from backend.embedding.embedder import LocalEmbedder
from backend.evaluation.dataset_loader import load_evaluation_cases
from backend.evaluation.metrics import RetrievalMetrics, calculate_metrics
from backend.evaluation.retrieval_evaluator import RetrievalEvaluator
from backend.retrieval.bm25_retriever import BM25Retriever
from backend.retrieval.dense_retriever import DenseRetriever
from backend.retrieval.hybrid_retriever import HybridRetriever
from backend.vector_store.qdrant_store import QdrantVectorStore


PROJECT_ROOT = Path(__file__).resolve().parents[1]

DATASET_PATH = (
    PROJECT_ROOT
    / "benchmarks"
    / "retrieval"
    / "ci"
    / "cases.jsonl"
)

BASELINE_PATH = (
    PROJECT_ROOT
    / "benchmarks"
    / "retrieval"
    / "ci"
    / "baseline.json"
)

CHUNKS_PATH = (
    PROJECT_ROOT
    / "benchmarks"
    / "retrieval"
    / "ci"
    / "chunks.jsonl"
)

COLLECTION_NAME = "enterprise_knowledge_ci_bge_small"

GATED_METRICS = (
    "hit_at_1",
    "hit_at_10",
    "recall_at_10",
    "ndcg_at_10",
    "mrr",
)


def load_baseline() -> tuple[
    dict[str, float],
    float,
]:
    with BASELINE_PATH.open(
        "r",
        encoding="utf-8",
    ) as file:
        payload = json.load(file)

    metrics = payload["metrics"]

    baseline = {
        metric: float(metrics[metric])
        for metric in GATED_METRICS
    }

    tolerance = float(
        payload["regression_tolerance"]
    )

    return baseline, tolerance


def build_retriever() -> HybridRetriever:
    serializer = ChunkSerializer()

    chunks = serializer.load_jsonl(
        CHUNKS_PATH,
    )

    embedder = LocalEmbedder(
        model_name="BAAI/bge-small-en-v1.5",
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

    return HybridRetriever(
        dense_retriever=dense_retriever,
        bm25_retriever=bm25_retriever,
        rrf_k=60,
        dense_weight=0.7,
        bm25_weight=0.3,
    )


def evaluate_current() -> RetrievalMetrics:
    cases = load_evaluation_cases(
        DATASET_PATH,
    )

    if not cases:
        raise ValueError(
            "No active evaluation cases found."
        )

    retriever = build_retriever()

    evaluator = RetrievalEvaluator(
        retriever=retriever,
    )

    results = evaluator.evaluate(
        cases=cases,
        top_k=10,
    )

    return calculate_metrics(
        results,
    )


def check_regression(
    current: RetrievalMetrics,
    baseline: dict[str, float],
    tolerance: float,
) -> bool:
    passed = True

    print()
    print("=" * 80)
    print("RETRIEVAL REGRESSION CHECK")
    print("=" * 80)

    for metric in GATED_METRICS:
        current_value = float(
            getattr(current, metric)
        )

        baseline_value = baseline[metric]

        minimum_allowed = (
            baseline_value
            - tolerance
        )

        metric_passed = (
            current_value
            >= minimum_allowed
        )

        status = (
            "PASS"
            if metric_passed
            else "FAIL"
        )

        print(
            f"{metric:<15} "
            f"baseline={baseline_value:.4f} "
            f"current={current_value:.4f} "
            f"minimum={minimum_allowed:.4f} "
            f"{status}"
        )

        if not metric_passed:
            passed = False

    return passed


def main() -> None:
    baseline, tolerance = load_baseline()

    current = evaluate_current()

    passed = check_regression(
        current=current,
        baseline=baseline,
        tolerance=tolerance,
    )

    print()

    if passed:
        print(
            "Retrieval regression check passed."
        )
        return

    print(
        "Retrieval regression detected."
    )

    sys.exit(1)


if __name__ == "__main__":
    main()