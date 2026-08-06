from backend.embedding.embedder import LocalEmbedder
from backend.retrieval.dense_retriever import DenseRetriever
from backend.vector_store.qdrant_store import QdrantVectorStore


COLLECTION_NAME = "enterprise_knowledge_fixed_bge_small"


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

    print("=" * 80)
    print("ENTERPRISE KNOWLEDGE DENSE RETRIEVAL")
    print("=" * 80)
    print("Type 'exit' to stop.")

    while True:
        print()
        query = input("Query: ").strip()

        if query.lower() in {
            "exit",
            "quit",
            "q",
        }:
            print("Stopped.")
            break

        if not query:
            print("Query must not be empty.")
            continue

        results = retriever.retrieve(
            query=query,
            top_k=20,
        )

        print()
        print(f"Results: {len(results)}")

        for result in results:
            print()
            print("-" * 80)
            print(f"Rank          : {result.rank}")
            print(f"Score         : {result.score:.6f}")
            print(f"Source        : {result.source}")
            print(f"Title         : {result.title}")
            print(f"Filename      : {result.filename}")
            print(f"Relative path : {result.relative_path}")
            print(f"Chunk index   : {result.chunk_index}")
            print(f"Token count   : {result.token_count}")
            print(f"Content       : {result.content[:700]}")


if __name__ == "__main__":
    main()