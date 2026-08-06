from pathlib import Path

from backend.chunking.serializer import ChunkSerializer


def main() -> None:

    serializer = ChunkSerializer()

    total_chunks = 0
    total_batches = 0

    for batch in serializer.iter_jsonl_batches(
        input_path=Path(
            "data/processed/chunks_fixed.jsonl"
        ),
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

    assert total_chunks == 33_017

    print()
    print("All chunk batch iterator checks passed.")


if __name__ == "__main__":
    main()