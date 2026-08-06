from pathlib import Path

from backend.indexing.pipeline import IndexingPipeline


COLLECTION_NAME = (
    "enterprise_knowledge_fixed_bge_small"
)


def main() -> None:

    pipeline = IndexingPipeline(
        input_path=Path(
            "data/processed/chunks_fixed.jsonl"
        ),
        collection_name=COLLECTION_NAME,
        batch_size=64,
    )

    indexed_count = pipeline.run()

    collection_info = (
        pipeline.vector_store.client.get_collection(
            collection_name=COLLECTION_NAME,
        )
    )

    print()
    print("=" * 60)
    print("QDRANT INDEXING COMPLETED")
    print("=" * 60)
    print(f"Indexed chunks : {indexed_count:,}")
    print(
        f"Collection size: "
        f"{collection_info.points_count or 0:,}"
    )
    print(f"Status         : {collection_info.status}")


if __name__ == "__main__":
    main()