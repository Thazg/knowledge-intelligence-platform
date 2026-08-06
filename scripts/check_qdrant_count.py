from backend.embedding.embedder import LocalEmbedder
from backend.vector_store.qdrant_store import QdrantVectorStore


COLLECTION_NAME = "enterprise_knowledge_fixed_bge_small"


def main() -> None:
    embedder = LocalEmbedder(
        model_name="BAAI/bge-small-en-v1.5",
    )

    store = QdrantVectorStore(
        collection_name=COLLECTION_NAME,
        vector_size=embedder.dimension,
    )

    info = store.client.get_collection(
        collection_name=COLLECTION_NAME,
    )

    print(f"Collection   : {COLLECTION_NAME}")
    print(f"Points count : {info.points_count}")
    print(f"Vectors count: {info.indexed_vectors_count}")


if __name__ == "__main__":
    main()