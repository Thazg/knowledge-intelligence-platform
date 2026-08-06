from collections import Counter
from pathlib import Path

from backend.ingestion.discovery import DocumentDiscovery


def main() -> None:
    discovery = DocumentDiscovery(Path("data/raw"))

    documents = discovery.discover()

    extension_counter = Counter(document.extension for document in documents)
    source_counter = Counter(document.source for document in documents)

    print("=" * 50)
    print("Discovery Summary")
    print("=" * 50)

    print(f"Sources   : {len(source_counter)}")
    print(f"Documents : {len(documents):,}")
    print("\nBy Extension")
    print("-" * 50)

    for extension, count in extension_counter.most_common():
        print(f"{extension:<10} {count:>8,}")

    print("\nBy Source")
    print("-" * 50)

    for source, count in source_counter.most_common():
        print(f"{source:<20} {count:>8,}")


if __name__ == "__main__":
    main()
