from __future__ import annotations

import argparse
import json
from pathlib import Path
from typing import Any


PROJECT_ROOT = Path(__file__).resolve().parents[1]

DEFAULT_PROPOSED_PATH = (
    PROJECT_ROOT
    / "benchmarks"
    / "retrieval"
    / "proposed_cases.jsonl"
)

DEFAULT_CASES_PATH = (
    PROJECT_ROOT
    / "benchmarks"
    / "retrieval"
    / "cases.jsonl"
)


def load_jsonl(path: Path) -> list[dict[str, Any]]:
    if not path.exists():
        return []

    records: list[dict[str, Any]] = []

    with path.open("r", encoding="utf-8") as file:
        for line_number, line in enumerate(file, start=1):
            if not line.strip():
                continue

            try:
                records.append(json.loads(line))
            except json.JSONDecodeError as exc:
                raise RuntimeError(
                    f"Invalid JSON in {path} at line {line_number}: {exc}"
                ) from exc

    return records


def write_jsonl(
    records: list[dict[str, Any]],
    path: Path,
) -> None:
    path.parent.mkdir(
        parents=True,
        exist_ok=True,
    )

    with path.open("w", encoding="utf-8") as file:
        for record in records:
            file.write(
                json.dumps(
                    record,
                    ensure_ascii=False,
                )
                + "\n"
            )


def main() -> None:
    parser = argparse.ArgumentParser(
        description=(
            "Promote validated proposed benchmark cases "
            "into the official benchmark dataset."
        )
    )

    parser.add_argument(
        "--proposed",
        type=Path,
        default=DEFAULT_PROPOSED_PATH,
    )

    parser.add_argument(
        "--cases",
        type=Path,
        default=DEFAULT_CASES_PATH,
    )

    args = parser.parse_args()

    proposed_cases = load_jsonl(
        args.proposed
    )

    existing_cases = load_jsonl(
        args.cases
    )

    print("=" * 72)
    print("PROMOTE BENCHMARK CASES")
    print("=" * 72)

    print(
        f"Existing official cases: {len(existing_cases)}"
    )

    print(
        f"Proposed cases:          {len(proposed_cases)}"
    )

    if not proposed_cases:
        print("No proposed cases to promote.")
        return

    official_by_id: dict[
        str,
        dict[str, Any],
    ] = {}

    official_order: list[str] = []

    for case in existing_cases:
        case_id = case.get("case_id")

        if not case_id:
            raise RuntimeError(
                "Official benchmark contains a case without case_id."
            )

        if case_id in official_by_id:
            raise RuntimeError(
                f"Duplicate official case_id: {case_id}"
            )

        official_by_id[case_id] = case
        official_order.append(case_id)

    added = 0
    updated = 0

    for proposed in proposed_cases:
        case_id = proposed.get("case_id")

        if not case_id:
            raise RuntimeError(
                "Proposed benchmark contains a case without case_id."
            )

        promoted = dict(proposed)
        promoted["status"] = "active"

        if case_id in official_by_id:
            official_by_id[case_id] = promoted
            updated += 1

            print(
                f"[UPDATE] {case_id}"
            )

        else:
            official_by_id[case_id] = promoted
            official_order.append(case_id)
            added += 1

            print(
                f"[ADD]    {case_id}"
            )

    output_records = [
        official_by_id[case_id]
        for case_id in official_order
    ]

    write_jsonl(
        output_records,
        args.cases,
    )

    print()
    print("=" * 72)
    print("SUMMARY")
    print("=" * 72)

    print(
        f"Added:   {added}"
    )

    print(
        f"Updated: {updated}"
    )

    print(
        f"Total:   {len(output_records)}"
    )

    print(
        f"Output:  {args.cases}"
    )


if __name__ == "__main__":
    main()