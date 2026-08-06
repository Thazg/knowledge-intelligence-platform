from qdrant_client import QdrantClient


COLLECTION_NAME = "enterprise_knowledge_fixed_bge_small"


def main() -> None:
    client = QdrantClient(
        url="http://localhost:6333",
    )

    if client.collection_exists(
        collection_name=COLLECTION_NAME,
    ):
        client.delete_collection(
            collection_name=COLLECTION_NAME,
        )
        print(f"Deleted: {COLLECTION_NAME}")
    else:
        print("Collection does not exist.")


if __name__ == "__main__":
    main()