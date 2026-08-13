import argparse
import json
from pathlib import Path

from backend.evaluation.dataset_loader import (
    load_evaluation_cases,
)
from backend.query_rewriting.query_rewriter import (
    QueryRewriter,
)


PROJECT_ROOT = Path(__file__).resolve().parents[1]

DEFAULT_DATASET_PATH = (
    PROJECT_ROOT
    / "benchmarks"
    / "retrieval"
    / "cases.jsonl"
)

DEFAULT_OUTPUT_PATH = (
    PROJECT_ROOT
    / "benchmarks"
    / "retrieval"
    / "query_rewrites.jsonl"
)


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description=(
            "Generate frozen query rewrites "
            "for retrieval evaluation cases."
        )
    )

    parser.add_argument(
        "--dataset",
        type=Path,
        default=DEFAULT_DATASET_PATH,
        help="Evaluation dataset JSONL path.",
    )

    parser.add_argument(
        "--output",
        type=Path,
        default=DEFAULT_OUTPUT_PATH,
        help="Output frozen rewrites JSONL path.",
    )

    parser.add_argument(
        "--all-statuses",
        action="store_true",
        help=(
            "Load cases regardless of status. "
            "Required for frozen routing datasets."
        ),
    )

    return parser.parse_args()


def resolve_path(path: Path) -> Path:
    if path.is_absolute():
        return path

    return PROJECT_ROOT / path


def load_existing_rewrites(
    path: Path,
) -> dict[str, dict]:
    if not path.exists():
        return {}

    records: dict[str, dict] = {}

    with path.open(
        "r",
        encoding="utf-8",
    ) as file:
        for line_number, line in enumerate(
            file,
            start=1,
        ):
            line = line.strip()

            if not line:
                continue

            try:
                record = json.loads(line)
            except json.JSONDecodeError as exc:
                raise ValueError(
                    f"Invalid JSON at line "
                    f"{line_number} in {path}"
                ) from exc

            case_id = record["case_id"]

            if case_id in records:
                raise ValueError(
                    f"Duplicate case_id in rewrite file: "
                    f"{case_id}"
                )

            records[case_id] = record

    return records


def validate_rewrites(
    original_query: str,
    rewrites: list[str],
    expected_count: int,
) -> None:
    if len(rewrites) != expected_count:
        raise ValueError(
            f"Expected {expected_count} rewrites, "
            f"received {len(rewrites)}."
        )

    normalized_original = (
        original_query.strip().casefold()
    )

    normalized_rewrites = [
        rewrite.strip().casefold()
        for rewrite in rewrites
    ]

    if any(
        not rewrite.strip()
        for rewrite in rewrites
    ):
        raise ValueError(
            "Rewrite must not be empty."
        )

    if normalized_original in normalized_rewrites:
        raise ValueError(
            "Rewrite must differ from original query."
        )

    if (
        len(set(normalized_rewrites))
        != len(normalized_rewrites)
    ):
        raise ValueError(
            "Duplicate rewrites generated."
        )


def main() -> None:
    args = parse_args()

    dataset_path = resolve_path(
        args.dataset
    )

    output_path = resolve_path(
        args.output
    )

    cases = load_evaluation_cases(
        dataset_path,
        active_only=not args.all_statuses,
    )

    if not cases:
        raise ValueError(
            "No evaluation cases found."
        )

    output_path.parent.mkdir(
        parents=True,
        exist_ok=True,
    )

    existing_rewrites = load_existing_rewrites(
        output_path
    )

    cases_to_generate = [
        case
        for case in cases
        if (
            case.case_id not in existing_rewrites
            or existing_rewrites[
                case.case_id
            ].get("original_query")
            != case.query
        )
    ]

    print("=" * 80)
    print(
        "GENERATING MISSING FROZEN QUERY REWRITES"
    )
    print("=" * 80)

    print(f"Dataset          : {dataset_path}")
    print(f"Output           : {output_path}")
    print(f"Cases            : {len(cases)}")
    print(
        f"Existing rewrites: "
        f"{len(existing_rewrites)}"
    )
    print(
        f"Rewrites to generate: "
        f"{len(cases_to_generate)}"
    )

    if not cases_to_generate:
        print()
        print(
            "No missing rewrites found."
        )
        return

    rewriter = QueryRewriter(
        model_name="qwen3:4b-instruct",
        num_rewrites=2,
    )

    new_records: list[dict] = []

    for index, case in enumerate(
        cases_to_generate,
        start=1,
    ):
        queries = rewriter.rewrite(
            case.query
        )

        rewrites = queries[1:]

        validate_rewrites(
            original_query=case.query,
            rewrites=rewrites,
            expected_count=2,
        )

        record = {
            "case_id": case.case_id,
            "original_query": case.query,
            "rewrites": rewrites,
        }

        new_records.append(record)

        print()
        print(
            f"[{index}/{len(cases_to_generate)}] "
            f"{case.case_id}"
        )
        print(
            f"Original : {case.query}"
        )

        for rewrite_index, rewrite in enumerate(
            rewrites,
            start=1,
        ):
            print(
                f"Rewrite {rewrite_index}: "
                f"{rewrite}"
            )

    for record in new_records:
        existing_rewrites[
            record["case_id"]
        ] = record

    with output_path.open(
        "w",
        encoding="utf-8",
    ) as output_file:
        for case in cases:
            record = existing_rewrites[
                case.case_id
            ]

            output_file.write(
                json.dumps(
                    record,
                    ensure_ascii=False,
                )
                + "\n"
            )

    print()
    print("=" * 80)
    print("DONE")
    print("=" * 80)
    print(
        f"Added rewrites: "
        f"{len(new_records)}"
    )
    print(
        f"Output        : "
        f"{output_path}"
    )


if __name__ == "__main__":
    main()