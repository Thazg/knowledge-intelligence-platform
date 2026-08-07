from pathlib import Path

from backend.chunking.serializer import ChunkSerializer
from backend.embedding.embedder import LocalEmbedder
from backend.evaluation.dataset_loader import (
    load_evaluation_cases,
)
from backend.evaluation.metrics import (
    calculate_metrics,
    calculate_metrics_by_category,
    print_metrics,
)
from backend.evaluation.retrieval_evaluator import (
    RetrievalEvaluator,
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

COLLECTION_NAME = (
    "enterprise_knowledge_fixed_bge_small"
)

EMBEDDING_MODEL = (
    "BAAI/bge-small-en-v1.5"
)

RERANKER_MODEL = (
    "mixedbread-ai/mxbai-rerank-base-v1"
)


def main() -> None:
    cases = load_evaluation_cases(
        DATASET_PATH,
        active_only=True,
    )

    if not cases:
        raise ValueError(
            "No active evaluation cases found."
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

    hybrid_retriever = HybridRetriever(
        dense_retriever=dense_retriever,
        bm25_retriever=bm25_retriever,
        rrf_k=60,
        dense_weight=0.7,
        bm25_weight=0.3,
    )

    reranker = CrossEncoderReranker(
        model_name=RERANKER_MODEL,
        batch_size=16,
    )

    reranked_retriever = (
        RerankedRetriever(
            base_retriever=hybrid_retriever,
            reranker=reranker,
            candidate_multiplier=4,
        )
    )

    evaluator = RetrievalEvaluator(
        retriever=reranked_retriever,
    )

    results = evaluator.evaluate(
        cases=cases,
        top_k=10,
    )

    overall_metrics = (
        calculate_metrics(
            results
        )
    )

    print_metrics(
        "RERANKED HYBRID RETRIEVAL EVALUATION",
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
            category_metrics[
                category
            ],
        )


if __name__ == "__main__":
    main()