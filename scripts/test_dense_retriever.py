from backend.embedding.embedder import LocalEmbedder
from backend.retrieval.dense_retriever import (
    DenseRetriever,
)
from backend.vector_store.qdrant_store import (
    QdrantVectorStore,
)


COLLECTION_NAME = (
    "enterprise_knowledge_fixed_bge_small"
)


def main() -> None:

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

    query = (
        "How do I expose a Kubernetes application "
        "using a Service?"
    )

    results = retriever.retrieve(
        query=query,
        top_k=5,
    )

    print("=" * 80)
    print("DENSE RETRIEVER TEST")
    print("=" * 80)
    print(f"Query   : {query}")
    print(f"Results : {len(results)}")

    for result in results:
        print()
        print("-" * 80)
        print(f"Rank          : {result.rank}")
        print(f"Score         : {result.score:.6f}")
        print(f"Source        : {result.source}")
        print(f"Filename      : {result.filename}")
        print(f"Relative path : {result.relative_path}")
        print(f"Chunk index   : {result.chunk_index}")
        print(f"Content       : {result.content[:500]}")

    assert len(results) > 0

    assert all(
        result.content
        for result in results
    )

    print()
    print("All dense retriever checks passed.")


if __name__ == "__main__":
    main()