import json
from pathlib import Path

from backend.chunking.serializer import ChunkSerializer
from backend.evaluation.retrieval_evaluator import (
    EvaluationCase,
    RetrievalEvaluator,
)
from backend.retrieval.bm25_retriever import BM25Retriever
from backend.evaluation.dataset_loader import (
    load_evaluation_cases,
)
from backend.evaluation.metrics import (
    calculate_metrics,
    calculate_metrics_by_category,
    print_metrics,
)

PROJECT_ROOT = Path(__file__).resolve().parents[1]
DATASET_PATH = Path(
    "benchmarks/retrieval/cases.jsonl"
)

COLLECTION_NAME = (
    "enterprise_knowledge_fixed_bge_small"
)

def mean(values: list[float]) -> float:
    if not values:
        return 0.0

    return sum(values) / len(values)


def main() -> None:

    cases = load_evaluation_cases(DATASET_PATH)

    if not cases:
        raise ValueError(
            "No active evaluation cases found."
        )

    chunks_path = (
        PROJECT_ROOT
        / "data"
        / "processed"
        / "chunks_fixed.jsonl"
    )

    serializer = ChunkSerializer()

    chunks = serializer.load_jsonl(
        chunks_path
    )

    print(f"Loaded chunks: {len(chunks):,}")

    retriever = BM25Retriever(
        chunks=chunks,
    )

    evaluator = RetrievalEvaluator(
        retriever=retriever,
    )

    results = evaluator.evaluate(
        cases=cases,
        top_k=10,
    )

    overall_metrics = calculate_metrics(
        results
    )

    print_metrics(
        "BM25 RETRIEVAL EVALUATION",
        overall_metrics,
    )

    category_metrics = (
        calculate_metrics_by_category(
            results
        )
    )

    for category in sorted(
        category_metrics
    ):
        print_metrics(
            f"CATEGORY: {category}",
            category_metrics[category],
        )
if __name__ == "__main__":
    main()