from collections import Counter
from statistics import mean, median

from backend.chunking.models import Chunk


class ChunkingReporter:

    def print_summary(
        self,
        chunks: list[Chunk],
        chunk_size: int,
    ) -> None:

        print()
        print("=" * 60)
        print("CHUNKING REPORT")
        print("=" * 60)

        if not chunks:
            print("No chunks available.")
            return

        token_counts = [
            chunk.token_count
            for chunk in chunks
        ]

        chunks_per_document = Counter(
            chunk.document_id
            for chunk in chunks
        )

        total_chunks = len(chunks)
        total_documents = len(chunks_per_document)
        total_tokens = sum(token_counts)

        average_tokens = mean(token_counts)
        median_tokens = median(token_counts)

        minimum_tokens = min(token_counts)
        maximum_tokens = max(token_counts)

        average_chunks_per_document = (
            total_chunks / total_documents
        )

        under_50 = sum(
            token_count < 50
            for token_count in token_counts
        )

        under_100 = sum(
            token_count < 100
            for token_count in token_counts
        )

        full_chunks = sum(
            token_count == chunk_size
            for token_count in token_counts
        )

        largest_document_id, largest_chunk_count = (
            chunks_per_document.most_common(1)[0]
        )

        largest_document_chunk = next(
            chunk
            for chunk in chunks
            if chunk.document_id == largest_document_id
        )

        print(f"Documents             : {total_documents:,}")
        print(f"Chunks                : {total_chunks:,}")
        print(f"Total chunk tokens    : {total_tokens:,}")
        print(
            f"Average chunks/doc    : "
            f"{average_chunks_per_document:,.2f}"
        )
        print(
            f"Average tokens/chunk  : "
            f"{average_tokens:,.2f}"
        )
        print(
            f"Median tokens/chunk   : "
            f"{median_tokens:,.2f}"
        )
        print(f"Minimum tokens        : {minimum_tokens:,}")
        print(f"Maximum tokens        : {maximum_tokens:,}")

        print()
        print("CHUNK LENGTH DISTRIBUTION")
        print("-" * 60)

        print(
            f"Chunks < 50 tokens    : "
            f"{under_50:,} "
            f"({under_50 / total_chunks:.2%})"
        )

        print(
            f"Chunks < 100 tokens   : "
            f"{under_100:,} "
            f"({under_100 / total_chunks:.2%})"
        )

        print(
            f"Full-size chunks      : "
            f"{full_chunks:,} "
            f"({full_chunks / total_chunks:.2%})"
        )

        print()
        print("DOCUMENT WITH MOST CHUNKS")
        print("-" * 60)
        print(f"Source        : {largest_document_chunk.source}")
        print(f"Filename      : {largest_document_chunk.filename}")
        print(
            f"Relative path : "
            f"{largest_document_chunk.relative_path}"
        )
        print(f"Chunk count   : {largest_chunk_count:,}")