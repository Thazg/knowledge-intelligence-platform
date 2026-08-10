from __future__ import annotations

from pathlib import Path

from backend.chunking.serializer import ChunkSerializer
from backend.embedding.embedder import LocalEmbedder
from backend.vector_store.qdrant_store import QdrantVectorStore


PROJECT_ROOT = Path(__file__).resolve().parents[1]

CHUNKS_PATH = (
    PROJECT_ROOT
    / "benchmarks"
    / "retrieval"
    / "ci"
    / "chunks.jsonl"
)

COLLECTION_NAME = "enterprise_knowledge_ci_bge_small"

EMBEDDING_MODEL = "BAAI/bge-small-en-v1.5"


def main() -> None:
    serializer = ChunkSerializer()

    chunks = serializer.load_jsonl(
        CHUNKS_PATH
    )

    if not chunks:
        raise ValueError(
            "CI retrieval corpus is empty."
        )

    print(
        f"Loaded CI chunks: {len(chunks):,}"
    )

    embedder = LocalEmbedder(
        model_name=EMBEDDING_MODEL,
    )

    print(
        f"Embedding dimension: "
        f"{embedder.dimension}"
    )

    texts = [
        chunk.content
        for chunk in chunks
    ]

    print(
        "Embedding CI corpus..."
    )

    embeddings = embedder.embed_documents(
        texts=texts,
        batch_size=32,
        show_progress_bar=True,
    )

    print(
        f"Embeddings created: "
        f"{len(embeddings):,}"
    )

    vector_store = QdrantVectorStore(
        collection_name=COLLECTION_NAME,
        vector_size=embedder.dimension,
    )

    if vector_store.collection_exists():
        print(
            f"Deleting existing collection: "
            f"{COLLECTION_NAME}"
        )

        vector_store.client.delete_collection(
            collection_name=COLLECTION_NAME,
        )

    print(
        f"Creating collection: "
        f"{COLLECTION_NAME}"
    )

    vector_store.create_collection()

    print(
        "Upserting CI chunks..."
    )

    vector_store.upsert_chunks(
        chunks=chunks,
        embeddings=embeddings,
        wait=True,
    )

    print()
    print("=" * 80)
    print(
        "CI RETRIEVAL COLLECTION READY"
    )
    print("=" * 80)

    print(
        f"Collection: {COLLECTION_NAME}"
    )

    print(
        f"Chunks: {len(chunks):,}"
    )

    print(
        f"Vector size: "
        f"{embedder.dimension}"
    )


if __name__ == "__main__":
    main()