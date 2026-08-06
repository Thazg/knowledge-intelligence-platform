from backend.embedding.embedder import LocalEmbedder
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

    store = QdrantVectorStore(
        collection_name=COLLECTION_NAME,
        vector_size=embedder.dimension,
    )

    query = (
        "How do Docker containers package "
        "applications and dependencies?"
    )

    query_embedding = embedder.embed_query(query)

    results = store.search(
        query_embedding=query_embedding,
        limit=5,
    )

    print("=" * 80)
    print("DENSE RETRIEVAL TEST")
    print("=" * 80)
    print(f"Query   : {query}")
    print(f"Results : {len(results)}")

    for rank, result in enumerate(
        results,
        start=1,
    ):
        payload = result.payload or {}

        content = str(
            payload.get("content", "")
        )

        print()
        print("-" * 80)
        print(f"Rank          : {rank}")
        print(f"Score         : {result.score:.6f}")
        print(
            f"Source        : "
            f"{payload.get('source')}"
        )
        print(
            f"Filename      : "
            f"{payload.get('filename')}"
        )
        print(
            f"Relative path : "
            f"{payload.get('relative_path')}"
        )
        print(
            f"Chunk index   : "
            f"{payload.get('chunk_index')}"
        )
        print(
            f"Content       : "
            f"{content[:400]}"
        )

    assert len(results) > 0

    assert all(
        result.payload is not None
        for result in results
    )

    assert all(
        "content" in result.payload
        for result in results
        if result.payload is not None
    )

    print()
    print("All dense retrieval checks passed.")


if __name__ == "__main__":
    main()