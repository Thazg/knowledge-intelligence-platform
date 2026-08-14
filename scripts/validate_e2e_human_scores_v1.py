from __future__ import annotations

import json
from collections import Counter
from pathlib import Path
from typing import Any


CASES_PATH = Path(
    "benchmarks/e2e/cases_v1.jsonl"
)

SCORES_PATH = Path(
    "benchmarks/e2e/review/human_scores_v1.jsonl"
)

CORE_SCORE_FIELDS = (
    "correctness",
    "faithfulness",
    "citation_correctness",
    "citation_completeness",
    "evidence_sufficiency",
)

OPTIONAL_SCORE_FIELDS = (
    "ambiguity_handling",
    "multi_source_synthesis",
    "abstention",
)

ALL_SCORE_FIELDS = (
    CORE_SCORE_FIELDS
    + OPTIONAL_SCORE_FIELDS
)

VALID_SCORES = {
    0,
    1,
    2,
    None,
}

VALID_VERDICTS = {
    "pass",
    "partial",
    "fail",
}


def load_jsonl(
    path: Path,
) -> list[dict[str, Any]]:
    records: list[dict[str, Any]] = []

    with path.open(
        "r",
        encoding="utf-8-sig",
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
                    f"Invalid JSON at "
                    f"{path}:{line_number}: {exc}"
                ) from exc

            if not isinstance(
                record,
                dict,
            ):
                raise ValueError(
                    f"{path}:{line_number} "
                    "must contain a JSON object."
                )

            records.append(record)

    return records


def require_score(
    record: dict[str, Any],
    field: str,
) -> int:
    value = record.get(field)

    if (
        value not in VALID_SCORES
        or value is None
        or isinstance(value, bool)
    ):
        raise ValueError(
            f"{record['case_id']}: "
            f"{field} must be 0, 1, or 2."
        )

    return value


def require_optional_score(
    record: dict[str, Any],
    field: str,
    *,
    applicable: bool,
) -> None:
    value = record.get(field)

    if value not in VALID_SCORES:
        raise ValueError(
            f"{record['case_id']}: "
            f"invalid {field} score: {value!r}"
        )

    if applicable:
        if (
            value is None
            or isinstance(value, bool)
        ):
            raise ValueError(
                f"{record['case_id']}: "
                f"{field} must be scored."
            )
    elif value is not None:
        raise ValueError(
            f"{record['case_id']}: "
            f"{field} must be null when "
            "not applicable."
        )


def scored_values(
    record: dict[str, Any],
) -> list[int]:
    values: list[int] = []

    for field in ALL_SCORE_FIELDS:
        value = record.get(field)

        if value is not None:
            values.append(value)

    return values


def validate_verdict_score_consistency(
    record: dict[str, Any],
) -> None:
    verdict = record["verdict"]
    values = scored_values(record)

    if not values:
        raise ValueError(
            f"{record['case_id']}: "
            "no scored dimensions."
        )

    if verdict == "pass":
        if any(
            value != 2
            for value in values
        ):
            raise ValueError(
                f"{record['case_id']}: "
                "PASS requires every "
                "applicable score to be 2."
            )

    elif verdict == "partial":
        if any(
            value == 0
            for value in values
        ):
            raise ValueError(
                f"{record['case_id']}: "
                "PARTIAL cannot contain "
                "a score of 0."
            )

        if 1 not in values:
            raise ValueError(
                f"{record['case_id']}: "
                "PARTIAL requires at least "
                "one score of 1."
            )

    elif verdict == "fail":
        if 0 not in values:
            raise ValueError(
                f"{record['case_id']}: "
                "FAIL requires at least "
                "one score of 0."
            )


def validate() -> dict[str, Any]:
    cases = load_jsonl(
        CASES_PATH
    )

    scores = load_jsonl(
        SCORES_PATH
    )

    case_by_id = {
        case["case_id"]: case
        for case in cases
    }

    expected_ids = set(
        case_by_id
    )

    score_ids = [
        record.get("case_id")
        for record in scores
    ]

    counts = Counter(
        score_ids
    )

    duplicate_ids = sorted(
        case_id
        for case_id, count
        in counts.items()
        if count > 1
    )

    if duplicate_ids:
        raise ValueError(
            "Duplicate score case IDs: "
            f"{duplicate_ids}"
        )

    observed_ids = set(
        score_ids
    )

    missing_ids = sorted(
        expected_ids - observed_ids
    )

    unknown_ids = sorted(
        observed_ids - expected_ids
    )

    if missing_ids:
        raise ValueError(
            "Missing score cases: "
            f"{missing_ids}"
        )

    if unknown_ids:
        raise ValueError(
            "Unknown score cases: "
            f"{unknown_ids}"
        )

    for record in scores:
        case_id = record["case_id"]
        case = case_by_id[case_id]

        if (
            record.get("category")
            != case.get("category")
        ):
            raise ValueError(
                f"{case_id}: category mismatch."
            )

        if (
            record.get(
                "expected_behavior"
            )
            != case.get(
                "expected_behavior"
            )
        ):
            raise ValueError(
                f"{case_id}: expected_behavior "
                "mismatch."
            )

        for field in CORE_SCORE_FIELDS:
            require_score(
                record,
                field,
            )

        behavior = record[
            "expected_behavior"
        ]

        category = record[
            "category"
        ]

        require_optional_score(
            record,
            "ambiguity_handling",
            applicable=(
                behavior
                == "qualified_answer"
            ),
        )

        require_optional_score(
            record,
            "multi_source_synthesis",
            applicable=(
                category
                == "cross_tool"
            ),
        )

        require_optional_score(
            record,
            "abstention",
            applicable=(
                behavior
                == "insufficient_evidence"
            ),
        )

        verdict = record.get(
            "verdict"
        )

        if verdict not in VALID_VERDICTS:
            raise ValueError(
                f"{case_id}: invalid verdict "
                f"{verdict!r}."
            )

        blocker = record.get(
            "blocker"
        )

        if not isinstance(
            blocker,
            bool,
        ):
            raise ValueError(
                f"{case_id}: blocker "
                "must be boolean."
            )

        notes = record.get(
            "notes"
        )

        if (
            not isinstance(notes, str)
            or not notes.strip()
        ):
            raise ValueError(
                f"{case_id}: notes "
                "must be non-empty."
            )

        validate_verdict_score_consistency(
            record
        )

    verdict_counts = Counter(
        record["verdict"]
        for record in scores
    )

    blocker_ids = sorted(
        record["case_id"]
        for record in scores
        if record["blocker"]
    )

    return {
        "case_count": len(scores),
        "pass_count": (
            verdict_counts["pass"]
        ),
        "partial_count": (
            verdict_counts["partial"]
        ),
        "fail_count": (
            verdict_counts["fail"]
        ),
        "blocker_case_ids": blocker_ids,
    }


def main() -> None:
    summary = validate()

    print("=" * 72)
    print(
        "E2E HUMAN SCORES V1 VALIDATION"
    )
    print("=" * 72)
    print(
        "Cases    :",
        summary["case_count"],
    )
    print(
        "Pass     :",
        summary["pass_count"],
    )
    print(
        "Partial  :",
        summary["partial_count"],
    )
    print(
        "Fail     :",
        summary["fail_count"],
    )
    print(
        "Blockers :",
        summary["blocker_case_ids"],
    )
    print()
    print("VALID")


if __name__ == "__main__":
    main()
