from pathlib import Path

from backend.embedding.embedder import LocalEmbedder
from backend.query_rewriting import QueryRewriter
from backend.retrieval.bm25_retriever import BM25Retriever
from backend.retrieval.dense_retriever import DenseRetriever
from backend.retrieval.hybrid_retriever import HybridRetriever
from backend.retrieval.multi_query_retriever import MultiQueryRetriever
from backend.vector_store.qdrant_store import QdrantVectorStore
from scripts.evaluate_reranked_retrieval import PROJECT_ROOT
from backend.chunking.serializer import ChunkSerializer

def main() -> None:
    embedder = LocalEmbedder(
        model_name="BAAI/bge-small-en-v1.5",
    )

    vector_store = QdrantVectorStore(
        collection_name="enterprise_knowledge_fixed_bge_small",
        vector_size=384,
    )

    dense_retriever = DenseRetriever(
        embedder=embedder,
        vector_store=vector_store,
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

    query_rewriter = QueryRewriter(
        model_name="qwen3:4b-instruct",
        num_rewrites=2,
    )

    retriever = MultiQueryRetriever(
        base_retriever=hybrid_retriever,
        query_rewriter=query_rewriter,
        rrf_k=60,
        candidate_multiplier=5,
    )

    query = "How does LangGraph persist state between executions?"

    results = retriever.retrieve(
        query=query,
        top_k=5,
        max_chunks_per_document=1,
    )

    print("=" * 80)
    print("MULTI-QUERY RETRIEVAL TEST")
    print("=" * 80)

    print()
    print(f"Query: {query}")

    print()
    print("Generated queries:")

    generated_queries = query_rewriter.rewrite(query)

    for index, generated_query in enumerate(generated_queries):
        label = "ORIGINAL" if index == 0 else f"REWRITE {index}"
        print(f"{label}: {generated_query}")

    print()
    print("Final results:")

    for result in results:
        print()
        print(f"Rank   : {result.rank}")
        print(f"Score  : {result.score:.6f}")
        print(f"Source : {result.source}")
        print(f"Path   : {result.relative_path}")
        print(f"Title  : {result.title}")

    assert len(results) == 5

    document_ids = [
        result.document_id
        for result in results
    ]

    assert len(document_ids) == len(set(document_ids))

    assert [result.rank for result in results] == [
        1,
        2,
        3,
        4,
        5,
    ]

    print()
    print("Test passed.")


if __name__ == "__main__":
    main()