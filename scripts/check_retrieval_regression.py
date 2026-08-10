from __future__ import annotations

import argparse
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


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description=(
            "Run the retrieval regression gate against a benchmark baseline."
        )
    )

    parser.add_argument(
        "--dataset",
        type=Path,
        default=DATASET_PATH,
        help="Path to retrieval benchmark cases JSONL.",
    )

    parser.add_argument(
        "--chunks",
        type=Path,
        default=CHUNKS_PATH,
        help="Path to chunks JSONL used by BM25.",
    )

    parser.add_argument(
        "--collection",
        default=COLLECTION_NAME,
        help="Qdrant collection used by dense retrieval.",
    )

    parser.add_argument(
        "--baseline",
        type=Path,
        default=BASELINE_PATH,
        help=(
            "Path to either the fast CI baseline JSON "
            "or the full benchmark manifest JSON."
        ),
    )

    return parser.parse_args()


def load_baseline(
    baseline_path: Path = BASELINE_PATH,
) -> tuple[
    dict[str, float],
    float,
]:
    with baseline_path.open(
        "r",
        encoding="utf-8",
    ) as file:
        payload = json.load(file)

    if "metrics" in payload:
        metrics = payload["metrics"]
        tolerance = float(
            payload["regression_tolerance"]
        )
    elif "baseline" in payload:
        metrics = payload["baseline"]
        tolerance = float(
            payload["regression"]["tolerance"]
        )
    else:
        raise ValueError(
            "Unsupported retrieval baseline format."
        )

    baseline = {
        metric: float(metrics[metric])
        for metric in GATED_METRICS
    }

    return baseline, tolerance


def build_retriever(
    chunks_path: Path = CHUNKS_PATH,
    collection_name: str = COLLECTION_NAME,
) -> HybridRetriever:
    serializer = ChunkSerializer()

    chunks = serializer.load_jsonl(
        chunks_path,
    )

    embedder = LocalEmbedder(
        model_name="BAAI/bge-small-en-v1.5",
    )

    vector_store = QdrantVectorStore(
        collection_name=collection_name,
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


def evaluate_current(
    dataset_path: Path = DATASET_PATH,
    chunks_path: Path = CHUNKS_PATH,
    collection_name: str = COLLECTION_NAME,
) -> RetrievalMetrics:
    cases = load_evaluation_cases(
        dataset_path,
    )

    if not cases:
        raise ValueError(
            "No active evaluation cases found."
        )

    retriever = build_retriever(
        chunks_path=chunks_path,
        collection_name=collection_name,
    )

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
    args = parse_args()

    baseline, tolerance = load_baseline(
        args.baseline,
    )

    current = evaluate_current(
        dataset_path=args.dataset,
        chunks_path=args.chunks,
        collection_name=args.collection,
    )

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