from pathlib import Path

from backend.embedding.pipeline import (
    EmbeddingPipeline,
)
from backend.vector_store.qdrant_store import (
    QdrantVectorStore,
)


COLLECTION_NAME = (
    "enterprise_knowledge_fixed_bge_small"
)


def main() -> None:

    embedding_pipeline = EmbeddingPipeline(
        input_path=Path(
            "data/processed/chunks_fixed.jsonl"
        ),
        batch_size=32,
    )

    chunks, embeddings = embedding_pipeline.run(
        limit=100,
        show_progress_bar=True,
    )

    store = QdrantVectorStore(
        collection_name=COLLECTION_NAME,
        vector_size=(
            embedding_pipeline.embedder.dimension
        ),
    )

    store.create_collection()

    uploaded_count = store.upsert_chunks(
        chunks=chunks,
        embeddings=embeddings,
        wait=True,
    )

    collection_info = store.client.get_collection(
        collection_name=COLLECTION_NAME,
    )

    print()
    print("=" * 60)
    print("QDRANT UPSERT TEST")
    print("=" * 60)
    print(f"Uploaded : {uploaded_count:,}")
    print(
        f"Points   : "
        f"{collection_info.points_count or 0:,}"
    )
    print(f"Status   : {collection_info.status}")

    assert uploaded_count == 100
    assert collection_info.points_count == 100

    print()
    print("All Qdrant upsert checks passed.")


if __name__ == "__main__":
    main()