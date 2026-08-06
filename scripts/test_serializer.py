from pathlib import Path

from backend.ingestion.serializer import DocumentSerializer


def main() -> None:
    serializer = DocumentSerializer()

    documents = serializer.load_jsonl(Path("data/processed/documents.jsonl"))

    print(f"Loaded documents: {len(documents):,}")


if __name__ == "__main__":
    main()
