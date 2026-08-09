from pathlib import Path

from backend.chunking.serializer import ChunkSerializer


def main() -> None:

    serializer = ChunkSerializer()

    chunks = serializer.load_jsonl(
        Path("data/processed/chunks_fixed.jsonl")
    )

    print("=" * 60)
    print("CHUNK SERIALIZER TEST")
    print("=" * 60)
    print(f"Loaded chunks: {len(chunks):,}")

    if chunks:
        first_chunk = chunks[0]

        print()
        print("FIRST CHUNK")
        print("-" * 60)
        print(f"Chunk ID    : {first_chunk.chunk_id[:16]}...")
        print(f"Document ID : {first_chunk.document_id[:16]}...")
        print(f"Filename    : {first_chunk.filename}")
        print(f"Chunk index : {first_chunk.chunk_index}")
        print(f"Token count : {first_chunk.token_count}")
        print(f"Content     : {first_chunk.content[:300]}")


if __name__ == "__main__":
    main()
