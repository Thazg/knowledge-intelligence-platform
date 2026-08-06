import json
from pathlib import Path


DOCUMENTS_PATH = Path(
    "data/processed/documents.jsonl"
)


def main() -> None:
    keyword = input(
        "Keyword: "
    ).strip().lower()

    if not keyword:
        print("Keyword must not be empty.")
        return

    matches: list[dict] = []

    with DOCUMENTS_PATH.open(
        "r",
        encoding="utf-8",
    ) as file:
        for line in file:
            record = json.loads(line)

            searchable_text = " ".join(
                [
                    str(record.get("title", "")),
                    str(record.get("filename", "")),
                    str(record.get("relative_path", "")),
                ]
            ).lower()

            if keyword in searchable_text:
                matches.append(record)

    print()
    print(f"Matches: {len(matches):,}")

    for record in matches[:50]:
        print("-" * 80)
        print(f"Source : {record.get('source')}")
        print(f"Title  : {record.get('title')}")
        print(f"Path   : {record.get('relative_path')}")


if __name__ == "__main__":
    main()