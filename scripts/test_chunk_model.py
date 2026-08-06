from backend.chunking.models import Chunk


def main() -> None:
    chunk = Chunk(
        chunk_id="chunk-001",
        document_id="document-001",
        content="Docker containers package applications and dependencies.",
        chunk_index=0,
        token_count=9,
        source="docker",
        filename="containers.md",
        relative_path="docker/guides/containers.md",
        title="Docker Containers",
    )

    print(chunk)


if __name__ == "__main__":
    main()
