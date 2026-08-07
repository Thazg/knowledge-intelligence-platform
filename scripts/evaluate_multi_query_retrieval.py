import json
from pathlib import Path

from backend.chunking.serializer import ChunkSerializer
from backend.embedding.embedder import LocalEmbedder
from backend.evaluation.retrieval_evaluator import (
    EvaluationCase,
    RetrievalEvaluator,
)
from backend.query_rewriting.frozen_query_rewriter import (
    FrozenQueryRewriter,
)
from backend.query_rewriting.query_rewriter import QueryRewriter
from backend.retrieval.bm25_retriever import BM25Retriever
from backend.retrieval.dense_retriever import DenseRetriever
from backend.retrieval.hybrid_retriever import HybridRetriever
from backend.retrieval.multi_query_retriever import MultiQueryRetriever
from backend.vector_store.qdrant_store import QdrantVectorStore
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
    "backend/evaluation/datasets/retrieval_cases.jsonl"
)
CHUNKS_PATH = (
    PROJECT_ROOT
    / "data"
    / "processed"
    / "chunks_fixed.jsonl"
)
COLLECTION_NAME = "enterprise_knowledge_fixed_bge_small"

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
        CHUNKS_PATH
    )

    print(f"Loaded chunks: {len(chunks):,}")

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
    
    hybrid_retriever = HybridRetriever(
        dense_retriever=dense_retriever,
        bm25_retriever=bm25_retriever,
        rrf_k=60,
        dense_weight=0.7,
        bm25_weight=0.3,
    )
    
    rewrites_path = (
        PROJECT_ROOT
        / "backend"
        / "evaluation"
        / "datasets"
        / "query_rewrites.jsonl"
    )

    query_rewriter = FrozenQueryRewriter(
        rewrites_path=rewrites_path,
    )

    retriever = MultiQueryRetriever(
        base_retriever=hybrid_retriever,
        query_rewriter=query_rewriter,
        rrf_k=60,
        candidate_multiplier=5,
        query_weights=[
            1.0,  # original
            0.7,  # rewrite 1
            0.7,  # rewrite 2
        ],
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
        "MULTI-QUERY RETRIEVAL EVALUATION",
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