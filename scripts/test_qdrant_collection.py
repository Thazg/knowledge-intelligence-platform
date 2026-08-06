from backend.vector_store.qdrant_store import (
    QdrantVectorStore,
)


def main() -> None:

    store = QdrantVectorStore(
        collection_name=(
            "enterprise_knowledge_fixed_bge_small"
        ),
        vector_size=384,
    )

    created = store.create_collection()

    collection_info = store.client.get_collection(
        collection_name=store.collection_name,
    )

    print("=" * 60)
    print("QDRANT COLLECTION TEST")
    print("=" * 60)
    print(f"Collection : {store.collection_name}")
    print(f"Created    : {created}")
    print(f"Status     : {collection_info.status}")
    print(
        f"Points     : "
        f"{collection_info.points_count or 0:,}"
    )
    print(
        f"Vector size: "
        f"{store.vector_size}"
    )

    assert store.collection_exists()

    print()
    print("All Qdrant collection checks passed.")


if __name__ == "__main__":
    main()