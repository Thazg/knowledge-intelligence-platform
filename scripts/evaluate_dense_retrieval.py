from pathlib import Path

from backend.embedding.embedder import LocalEmbedder
from backend.evaluation.retrieval_evaluator import RetrievalEvaluator
from backend.retrieval.dense_retriever import DenseRetriever
from backend.vector_store.qdrant_store import QdrantVectorStore
from backend.evaluation.dataset_loader import (
    load_evaluation_cases,
)
from backend.evaluation.metrics import (
    calculate_metrics,
    calculate_metrics_by_category,
    print_metrics,
)
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

    embedder = LocalEmbedder(
        model_name="BAAI/bge-small-en-v1.5",
    )

    vector_store = QdrantVectorStore(
        collection_name=COLLECTION_NAME,
        vector_size=embedder.dimension,
    )

    retriever = DenseRetriever(
        embedder=embedder,
        vector_store=vector_store,
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
        "DENSE RETRIEVAL EVALUATION",
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
