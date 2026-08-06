from pathlib import Path

from backend.chunking.serializer import ChunkSerializer
from backend.retrieval.bm25_retriever import BM25Retriever


CHUNKS_PATH = Path(
    "data/processed/chunks_fixed.jsonl"
)


def main() -> None:
    serializer = ChunkSerializer()

    chunks = serializer.load_jsonl(
        CHUNKS_PATH
    )

    print(f"Loaded chunks: {len(chunks):,}")

    retriever = BM25Retriever(
        chunks=chunks,
    )

    query = (
        "Explain Docker BuildKit and how it differs "
        "from the legacy builder."
    )

    results = retriever.retrieve(
        query=query,
        top_k=5,
        max_chunks_per_document=1,
        candidate_multiplier=5,
    )

    print("=" * 80)
    print("BM25 RETRIEVER TEST")
    print("=" * 80)
    print(f"Query   : {query}")
    print(f"Results : {len(results)}")

    for result in results:
        print()
        print("-" * 80)
        print(f"Rank          : {result.rank}")
        print(f"Score         : {result.score:.6f}")
        print(f"Source        : {result.source}")
        print(f"Title         : {result.title}")
        print(f"Relative path : {result.relative_path}")
        print(f"Chunk index   : {result.chunk_index}")
        print(f"Content       : {result.content[:500]}")

    assert results
    assert len(results) <= 5

    assert all(
        result.rank == index
        for index, result in enumerate(
            results,
            start=1,
        )
    )

    assert len({
        result.document_id
        for result in results
    }) == len(results)

    print()
    print("All BM25 retriever checks passed.")


if __name__ == "__main__":
    main()