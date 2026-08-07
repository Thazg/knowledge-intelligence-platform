from pathlib import Path

from backend.chunking.serializer import ChunkSerializer
from backend.embedding.embedder import LocalEmbedder
from backend.reranking.cross_encoder_reranker import (
    CrossEncoderReranker,
)
from backend.retrieval.bm25_retriever import BM25Retriever
from backend.retrieval.dense_retriever import DenseRetriever
from backend.retrieval.hybrid_retriever import HybridRetriever
from backend.retrieval.reranked_retriever import RerankedRetriever
from backend.vector_store.qdrant_store import QdrantVectorStore


COLLECTION_NAME = "enterprise_knowledge_fixed_bge_small"
CHUNKS_PATH = Path("data/processed/chunks_fixed.jsonl")


def main() -> None:
    chunks = ChunkSerializer().load_jsonl(CHUNKS_PATH)

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

    reranker = CrossEncoderReranker(
        model_name="cross-encoder/ms-marco-MiniLM-L6-v2",
        batch_size=16,
    )

    retriever = RerankedRetriever(
        base_retriever=hybrid_retriever,
        reranker=reranker,
        candidate_multiplier=4,
    )

    query = (
        "Explain Docker BuildKit and how it differs "
        "from the legacy builder."
    )

    results = retriever.retrieve(
        query=query,
        top_k=5,
        max_chunks_per_document=1,
    )

    print("=" * 80)
    print("RERANKED RETRIEVER TEST")
    print("=" * 80)
    print(f"Query   : {query}")
    print(f"Results : {len(results)}")

    for result in results:
        print()
        print("-" * 80)
        print(f"Rank          : {result.rank}")
        print(f"Rerank score  : {result.score:.6f}")
        print(f"Source        : {result.source}")
        print(f"Title         : {result.title}")
        print(f"Relative path : {result.relative_path}")
        print(f"Chunk index   : {result.chunk_index}")
        print(f"Content       : {result.content[:500]}")

    assert results
    assert len(results) == 5

    assert all(
        result.rank == expected_rank
        for expected_rank, result in enumerate(
            results,
            start=1,
        )
    )

    assert len({
        result.document_id
        for result in results
    }) == len(results)

    print()
    print("All reranked retriever checks passed.")


if __name__ == "__main__":
    main()