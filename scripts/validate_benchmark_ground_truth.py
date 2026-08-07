from __future__ import annotations

import argparse
import json
from collections import defaultdict
from pathlib import Path
from typing import Any


PROJECT_ROOT = Path(__file__).resolve().parents[1]

DEFAULT_CHUNKS_PATH = (
    PROJECT_ROOT
    / "data"
    / "processed"
    / "chunks_fixed.jsonl"
)

DEFAULT_CASES_PATH = (
    PROJECT_ROOT
    / "benchmarks"
    / "retrieval"
    / "proposed_cases.jsonl"
)


def normalize_path(value: str) -> str:
    return value.replace("\\", "/").strip()


def load_document_index(
    chunks_path: Path,
) -> dict[tuple[str, str], int]:
    """
    Build:

        (source, path) -> number of chunks

    We only need metadata, so there is no reason to instantiate Chunk objects.
    """

    if not chunks_path.exists():
        raise FileNotFoundError(
            f"Chunks file not found: {chunks_path}"
        )

    document_index: dict[
        tuple[str, str],
        int,
    ] = defaultdict(int)

    with chunks_path.open(
        "r",
        encoding="utf-8",
    ) as file:
        for line_number, line in enumerate(
            file,
            start=1,
        ):
            if not line.strip():
                continue

            try:
                record = json.loads(line)
            except json.JSONDecodeError as exc:
                raise RuntimeError(
                    f"Invalid JSON in chunks file "
                    f"at line {line_number}: {exc}"
                ) from exc

            source = str(
                record.get("source", "")
            ).strip()

            path = normalize_path(
                str(
                    record.get(
                        "relative_path",
                        record.get("path", ""),
                    )
                )
            )

            if not source or not path:
                continue

            document_index[
                (source, path)
            ] += 1

    return dict(document_index)


def load_cases(
    path: Path,
) -> list[dict[str, Any]]:
    if not path.exists():
        raise FileNotFoundError(
            f"Cases file not found: {path}"
        )

    cases: list[
        dict[str, Any]
    ] = []

    with path.open(
        "r",
        encoding="utf-8",
    ) as file:
        for line_number, line in enumerate(
            file,
            start=1,
        ):
            if not line.strip():
                continue

            try:
                record = json.loads(line)
            except json.JSONDecodeError as exc:
                raise RuntimeError(
                    f"Invalid JSON in cases file "
                    f"at line {line_number}: {exc}"
                ) from exc

            cases.append(record)

    return cases


def validate_case(
    case: dict[str, Any],
    document_index: dict[
        tuple[str, str],
        int,
    ],
) -> list[str]:
    errors: list[str] = []

    case_id = case.get("case_id")

    if not case_id:
        errors.append(
            "missing case_id"
        )

    query = case.get("query")

    if not query:
        errors.append(
            "missing query"
        )

    category = case.get("category")

    if not category:
        errors.append(
            "missing category"
        )

    relevant_documents = (
        case.get("relevant_documents")
    )

    if (
        not isinstance(
            relevant_documents,
            list,
        )
        or not relevant_documents
    ):
        errors.append(
            "relevant_documents must be a non-empty list"
        )

        return errors

    seen_documents: set[
        tuple[str, str]
    ] = set()

    has_relevance_3 = False

    for index, document in enumerate(
        relevant_documents,
        start=1,
    ):
        prefix = (
            f"relevant_documents[{index}]"
        )

        if not isinstance(
            document,
            dict,
        ):
            errors.append(
                f"{prefix} is not an object"
            )
            continue

        source = str(
            document.get("source", "")
        ).strip()

        path = normalize_path(
            str(
                document.get("path", "")
            )
        )

        relevance = document.get(
            "relevance"
        )

        if not source:
            errors.append(
                f"{prefix}: missing source"
            )

        if not path:
            errors.append(
                f"{prefix}: missing path"
            )

        if relevance not in {
            1,
            2,
            3,
        }:
            errors.append(
                f"{prefix}: relevance must be 1, 2, or 3"
            )

        if relevance == 3:
            has_relevance_3 = True

        key = (
            source,
            path,
        )

        if key in seen_documents:
            errors.append(
                f"{prefix}: duplicate document "
                f"{source}:{path}"
            )

        seen_documents.add(key)

        if (
            source
            and path
            and key not in document_index
        ):
            errors.append(
                f"{prefix}: document not found in corpus: "
                f"{source}:{path}"
            )

    if not has_relevance_3:
        errors.append(
            "case has no relevance=3 document"
        )

    return errors


def main() -> None:
    parser = argparse.ArgumentParser(
        description=(
            "Validate benchmark ground truth "
            "against the indexed chunk corpus."
        )
    )

    parser.add_argument(
        "--cases",
        type=Path,
        default=DEFAULT_CASES_PATH,
    )

    parser.add_argument(
        "--chunks",
        type=Path,
        default=DEFAULT_CHUNKS_PATH,
    )

    args = parser.parse_args()

    print("=" * 72)
    print("BENCHMARK GROUND-TRUTH VALIDATOR")
    print("=" * 72)

    document_index = (
        load_document_index(
            args.chunks
        )
    )

    print(
        f"Unique documents in corpus: "
        f"{len(document_index):,}"
    )

    cases = load_cases(
        args.cases
    )

    print(
        f"Cases loaded: "
        f"{len(cases)}"
    )

    print()

    total_errors = 0
    passed = 0

    for case in cases:
        case_id = case.get(
            "case_id",
            "<missing-case-id>",
        )

        errors = validate_case(
            case,
            document_index,
        )

        if errors:
            total_errors += len(
                errors
            )

            print(
                f"[FAIL] {case_id}"
            )

            for error in errors:
                print(
                    f"       - {error}"
                )

        else:
            passed += 1

            relevant_documents = (
                case[
                    "relevant_documents"
                ]
            )

            total_chunks = sum(
                document_index[
                    (
                        document["source"],
                        normalize_path(
                            document["path"]
                        ),
                    )
                ]
                for document
                in relevant_documents
            )

            print(
                f"[PASS] {case_id} "
                f"({len(relevant_documents)} docs, "
                f"{total_chunks} chunks)"
            )

    print()
    print("=" * 72)
    print("SUMMARY")
    print("=" * 72)

    print(
        f"Cases:  {len(cases)}"
    )

    print(
        f"Passed: {passed}"
    )

    print(
        f"Failed: {len(cases) - passed}"
    )

    print(
        f"Errors: {total_errors}"
    )

    if total_errors > 0:
        raise SystemExit(1)


if __name__ == "__main__":
    main()