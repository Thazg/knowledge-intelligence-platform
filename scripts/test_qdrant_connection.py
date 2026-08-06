from qdrant_client import QdrantClient


def main() -> None:
    client = QdrantClient(
        host="localhost",
        port=6333,
    )

    collections = client.get_collections()

    print("=" * 60)
    print("QDRANT CONNECTION TEST")
    print("=" * 60)
    print("Connection: successful")
    print(f"Collections: {len(collections.collections)}")

    for collection in collections.collections:
        print(f"- {collection.name}")


if __name__ == "__main__":
    main()