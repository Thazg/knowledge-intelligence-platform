from pathlib import Path

from backend.chunking.fixed_token_chunker import FixedTokenChunker
from backend.ingestion.id_generator import generate_document_id
from backend.ingestion.models import Document
from backend.tokenization.tokenizer import DocumentTokenizer
from backend.chunking.serializer import ChunkSerializer

def main() -> None:
    tokenizer = DocumentTokenizer()

    chunker = FixedTokenChunker(
        tokenizer=tokenizer,
        chunk_size=20,
        chunk_overlap=5,
    )

    relative_path = Path("docker/guides/containers.md")

    document = Document(
        document_id=generate_document_id(
            source="docker",
            relative_path=relative_path,
        ),
        content=(
            "Docker containers package applications "
            "together with their dependencies. "
            "Containers provide isolated environments "
            "and make software deployment consistent "
            "across development and production systems. "
        )
        * 5,
        source="docker",
        filename="containers.md",
        relative_path=relative_path,
        extension=".md",
        title="Docker Containers",
        headings=[],
        word_count=70,
        token_count=0,
    )

    chunks = chunker.chunk_document(document)
    serializer = ChunkSerializer()

    serializer.save_jsonl(
        chunks=chunks,
        output_path=Path(
            "data/processed/test_chunks_fixed.jsonl"
        ),
    )

    print(f"Total chunks: {len(chunks)}")
    print()

    for chunk in chunks:
        actual_token_count = tokenizer.count_tokens(
            chunk.content
        )

        assert chunk.token_count == actual_token_count, (
            f"Token count mismatch at chunk {chunk.chunk_index}: "
            f"stored={chunk.token_count}, "
            f"actual={actual_token_count}"
        )

        assert actual_token_count <= chunker.chunk_size, (
            f"Chunk {chunk.chunk_index} exceeds chunk_size: "
            f"{actual_token_count} > {chunker.chunk_size}"
        )

        assert not chunk.content.startswith("##"), (
            f"Chunk {chunk.chunk_index} starts with "
            "a WordPiece continuation token."
        )

        print("=" * 60)
        print(f"Chunk index : {chunk.chunk_index}")
        print(f"Chunk ID    : {chunk.chunk_id[:16]}...")
        print(f"Token count : {chunk.token_count}")
        print(f"Actual count: {actual_token_count}")
        print(f"Content     : {chunk.content}")

    print()
    print("All chunk checks passed.")

if __name__ == "__main__":
    main()
