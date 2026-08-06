from pathlib import Path

from backend.ingestion.discovery import DocumentDiscovery
from backend.ingestion.parser import DocumentParser


def main() -> None:
    discovery = DocumentDiscovery(Path("data/raw"))

    documents = discovery.discover()

    if not documents:
        print("No documents found in data/raw")
        return

    parser = DocumentParser()

    document = parser.parse(documents[0])

    print("=" * 80)
    print(document.filename)
    print("=" * 80)

    print(document.content[:1000])


if __name__ == "__main__":
    main()
