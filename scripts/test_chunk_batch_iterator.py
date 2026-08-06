from pathlib import Path

from backend.chunking.serializer import ChunkSerializer


def main() -> None:

    serializer = ChunkSerializer()
    chunks_path = Path(
        "data/processed/chunks_fixed.jsonl"
    )
    expected_chunks = serializer.load_jsonl(chunks_path)

    total_chunks = 0
    total_batches = 0

    for batch in serializer.iter_jsonl_batches(
        input_path=chunks_path,
        batch_size=64,
    ):
        total_batches += 1
        total_chunks += len(batch)

        print(
            f"Batch {total_batches}: "
            f"{len(batch)} chunks"
        )

    print()
    print("=" * 60)
    print("CHUNK BATCH ITERATOR TEST")
    print("=" * 60)
    print(f"Total batches : {total_batches:,}")
    print(f"Total chunks  : {total_chunks:,}")

    assert total_chunks == len(expected_chunks)

    print()
    print("All chunk batch iterator checks passed.")


if __name__ == "__main__":
    main()
