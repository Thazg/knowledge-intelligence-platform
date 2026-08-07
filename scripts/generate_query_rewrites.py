import json
from pathlib import Path

from backend.evaluation.dataset_loader import (
    load_evaluation_cases,
)
from backend.query_rewriting.query_rewriter import (
    QueryRewriter,
)


PROJECT_ROOT = Path(__file__).resolve().parents[1]

DATASET_PATH = (
    PROJECT_ROOT
    / "backend"
    / "evaluation"
    / "datasets"
    / "retrieval_cases.jsonl"
)

OUTPUT_PATH = (
    PROJECT_ROOT
    / "backend"
    / "evaluation"
    / "datasets"
    / "query_rewrites.jsonl"
)


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

            records[case_id] = record

    return records


def main() -> None:
    cases = load_evaluation_cases(
        DATASET_PATH,
        active_only=True,
    )

    if not cases:
        raise ValueError(
            "No active evaluation cases found."
        )

    existing_rewrites = load_existing_rewrites(
        OUTPUT_PATH
    )

    missing_cases = [
        case
        for case in cases
        if case.case_id
        not in existing_rewrites
    ]

    print("=" * 80)
    print("GENERATING MISSING FROZEN QUERY REWRITES")
    print("=" * 80)
    print(f"Active cases     : {len(cases)}")
    print(
        f"Existing rewrites: "
        f"{len(existing_rewrites)}"
    )
    print(
        f"Missing rewrites : "
        f"{len(missing_cases)}"
    )

    if not missing_cases:
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
        missing_cases,
        start=1,
    ):
        queries = rewriter.rewrite(
            case.query
        )

        rewrites = queries[1:]

        record = {
            "case_id": case.case_id,
            "original_query": case.query,
            "rewrites": rewrites,
        }

        new_records.append(record)

        print()
        print(
            f"[{index}/{len(missing_cases)}] "
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

    with OUTPUT_PATH.open(
        "a",
        encoding="utf-8",
    ) as output_file:
        for record in new_records:
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
        f"{OUTPUT_PATH}"
    )


if __name__ == "__main__":
    main()