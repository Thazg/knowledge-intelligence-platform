from pathlib import Path

from backend.ingestion.discovery import DocumentDiscovery


TARGET_SUFFIX = (
    "content/manuals/build/buildkit/_index.md"
)


def main() -> None:

    raw_data_dir = Path("data/raw")

    target_file = (
        raw_data_dir
        / "docker"
        / "content"
        / "manuals"
        / "build"
        / "buildkit"
        / "_index.md"
    )

    print("=" * 80)
    print("BUILDKIT INGESTION TRACE")
    print("=" * 80)

    print(f"Raw file exists : {target_file.exists()}")
    print(f"Raw file size   : {target_file.stat().st_size:,}")

    discovery = DocumentDiscovery(raw_data_dir)

    discovered_files = discovery.discover()

    matches = [
        document_file
        for document_file in discovered_files
        if document_file.relative_path
        .as_posix()
        .lower()
        .endswith(TARGET_SUFFIX)
    ]

    print(f"Discovery matches: {len(matches)}")

    for document_file in matches:
        print()
        print(f"Source        : {document_file.source}")
        print(f"Filename      : {document_file.filename}")
        print(f"Relative path : {document_file.relative_path}")
        print(f"Extension     : {document_file.extension}")


if __name__ == "__main__":
    main()