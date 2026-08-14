from __future__ import annotations

import hashlib
import json
import re
from collections import Counter
from pathlib import Path
from statistics import mean
from typing import Any

if __package__:
    from scripts.validate_e2e_human_scores_v1 import (
        ALL_SCORE_FIELDS,
        validate,
    )
else:
    from validate_e2e_human_scores_v1 import (
        ALL_SCORE_FIELDS,
        validate,
    )


MANIFEST_PATH = Path(
    "benchmarks/e2e/v1/manifest.json"
)

CASES_PATH = Path(
    "benchmarks/e2e/cases_v1.jsonl"
)

RESULTS_PATH = Path(
    "benchmarks/e2e/results_v1.jsonl"
)

CORPUS_PATH = Path(
    "data/processed/chunks_fixed.jsonl"
)

PACKET_PATH = Path(
    "benchmarks/e2e/review/human_review_packet_v1.md"
)

SCORES_PATH = Path(
    "benchmarks/e2e/review/human_scores_v1.jsonl"
)

STRUCTURAL_REPORT_PATH = Path(
    "benchmarks/e2e/reports/e2e_structural_v1.json"
)

REPORT_PATH = Path(
    "benchmarks/e2e/reports/e2e_semantic_v1.json"
)


def load_json(path: Path) -> dict[str, Any]:
    value = json.loads(
        path.read_text(encoding="utf-8")
    )

    if not isinstance(value, dict):
        raise ValueError(
            f"{path} must contain a JSON object."
        )

    return value


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
                value = json.loads(line)
            except json.JSONDecodeError as exc:
                raise ValueError(
                    f"Invalid JSON at "
                    f"{path}:{line_number}: {exc}"
                ) from exc

            if not isinstance(value, dict):
                raise ValueError(
                    f"{path}:{line_number} "
                    "must contain a JSON object."
                )

            records.append(value)

    return records


def sha256_file(path: Path) -> str:
    return hashlib.sha256(
        path.read_bytes()
    ).hexdigest().upper()


def rate(
    numerator: int,
    denominator: int,
) -> float:
    if denominator == 0:
        return 0.0

    return round(
        numerator / denominator,
        4,
    )


def extract_packet_frozen_hashes(
    path: Path,
) -> dict[str, str]:
    text = path.read_text(
        encoding="utf-8"
    )

    results_match = re.search(
        r"- Results SHA256: `([A-F0-9]{64})`",
        text,
    )

    corpus_match = re.search(
        r"- Corpus SHA256: `([A-F0-9]{64})`",
        text,
    )

    if results_match is None:
        raise ValueError(
            "Review packet does not freeze "
            "the results SHA256."
        )

    if corpus_match is None:
        raise ValueError(
            "Review packet does not freeze "
            "the corpus SHA256."
        )

    return {
        "results_sha256": (
            results_match.group(1)
        ),
        "corpus_sha256": (
            corpus_match.group(1)
        ),
    }


def verdict_summary(
    records: list[dict[str, Any]],
) -> dict[str, Any]:
    counts = Counter(
        record["verdict"]
        for record in records
    )

    case_count = len(records)

    pass_count = counts["pass"]
    partial_count = counts["partial"]
    fail_count = counts["fail"]

    return {
        "case_count": case_count,
        "pass_count": pass_count,
        "partial_count": partial_count,
        "fail_count": fail_count,
        "pass_rate": rate(
            pass_count,
            case_count,
        ),
        "pass_or_partial_rate": rate(
            pass_count + partial_count,
            case_count,
        ),
    }


def grouped_breakdown(
    records: list[dict[str, Any]],
    field: str,
) -> dict[str, dict[str, Any]]:
    grouped: dict[
        str,
        list[dict[str, Any]],
    ] = {}

    for record in records:
        group = str(
            record[field]
        )

        grouped.setdefault(
            group,
            [],
        ).append(record)

    output: dict[
        str,
        dict[str, Any],
    ] = {}

    for group in sorted(grouped):
        group_records = grouped[group]

        summary = verdict_summary(
            group_records
        )

        blocker_ids = sorted(
            record["case_id"]
            for record in group_records
            if record["blocker"]
        )

        output[group] = {
            **summary,
            "blocker_case_ids": (
                blocker_ids
            ),
        }

    return output


def dimension_summary(
    records: list[dict[str, Any]],
) -> dict[str, dict[str, Any]]:
    output: dict[
        str,
        dict[str, Any],
    ] = {}

    for field in ALL_SCORE_FIELDS:
        values = [
            record[field]
            for record in records
            if record.get(field)
            is not None
        ]

        counts = Counter(values)

        output[field] = {
            "applicable_case_count": (
                len(values)
            ),
            "score_0_count": counts[0],
            "score_1_count": counts[1],
            "score_2_count": counts[2],
            "mean_score": (
                round(mean(values), 4)
                if values
                else None
            ),
        }

    return output


def semantic_gate(
    records: list[dict[str, Any]],
) -> dict[str, Any]:
    fail_case_ids = sorted(
        record["case_id"]
        for record in records
        if record["verdict"] == "fail"
    )

    blocker_case_ids = sorted(
        record["case_id"]
        for record in records
        if record["blocker"]
    )

    gate_pass = (
        not fail_case_ids
        and not blocker_case_ids
    )

    return {
        "pass": gate_pass,
        "fail_case_ids": fail_case_ids,
        "blocker_case_ids": (
            blocker_case_ids
        ),
        "reason": (
            "No FAIL verdicts or blocking "
            "semantic findings."
            if gate_pass
            else (
                "Semantic gate failed because "
                "the reviewed benchmark contains "
                "at least one FAIL verdict or "
                "blocking semantic finding."
            )
        ),
    }


def verify_frozen_inputs() -> dict[str, str]:
    packet_hashes = (
        extract_packet_frozen_hashes(
            PACKET_PATH
        )
    )

    actual_results_sha = (
        sha256_file(
            RESULTS_PATH
        )
    )

    actual_corpus_sha = (
        sha256_file(
            CORPUS_PATH
        )
    )

    if (
        packet_hashes[
            "results_sha256"
        ]
        != actual_results_sha
    ):
        raise RuntimeError(
            "Review packet/results mismatch: "
            f"packet={packet_hashes['results_sha256']}, "
            f"actual={actual_results_sha}"
        )

    if (
        packet_hashes[
            "corpus_sha256"
        ]
        != actual_corpus_sha
    ):
        raise RuntimeError(
            "Review packet/corpus mismatch: "
            f"packet={packet_hashes['corpus_sha256']}, "
            f"actual={actual_corpus_sha}"
        )

    structural_report = load_json(
        STRUCTURAL_REPORT_PATH
    )

    structural_evaluation = (
        structural_report.get(
            "evaluation",
            {}
        )
    )

    if (
        structural_evaluation.get(
            "structural_pass"
        )
        is not True
    ):
        raise RuntimeError(
            "Semantic evaluation requires "
            "a passing structural E2E report."
        )

    structural_results_sha = (
        structural_report.get(
            "inputs",
            {},
        ).get(
            "results_sha256"
        )
    )

    if (
        structural_results_sha
        != actual_results_sha
    ):
        raise RuntimeError(
            "Structural report/results mismatch: "
            f"structural={structural_results_sha}, "
            f"actual={actual_results_sha}"
        )

    return {
        "results_sha256": (
            actual_results_sha
        ),
        "corpus_sha256": (
            actual_corpus_sha
        ),
    }


def build_report() -> dict[str, Any]:
    validation_summary = validate()

    frozen_hashes = (
        verify_frozen_inputs()
    )

    manifest = load_json(
        MANIFEST_PATH
    )

    scores = load_jsonl(
        SCORES_PATH
    )

    cases = load_jsonl(
        CASES_PATH
    )

    case_ids = {
        case["case_id"]
        for case in cases
    }

    score_ids = {
        record["case_id"]
        for record in scores
    }

    if case_ids != score_ids:
        raise RuntimeError(
            "Case IDs differ between "
            "benchmark and human scores."
        )

    overall = verdict_summary(
        scores
    )

    blocker_case_ids = sorted(
        record["case_id"]
        for record in scores
        if record["blocker"]
    )

    partial_case_ids = sorted(
        record["case_id"]
        for record in scores
        if record["verdict"]
        == "partial"
    )

    fail_case_ids = sorted(
        record["case_id"]
        for record in scores
        if record["verdict"]
        == "fail"
    )

    gate = semantic_gate(
        scores
    )

    return {
        "report_version": (
            "e2e_semantic_v1"
        ),
        "benchmark_version": (
            manifest[
                "benchmark_version"
            ]
        ),
        "methodology": {
            "review_type": (
                "human_semantic_review"
            ),
            "score_scale": {
                "0": "fail",
                "1": "partial",
                "2": "pass",
                "null": "not_applicable",
            },
            "verdicts": [
                "pass",
                "partial",
                "fail",
            ],
            "external_knowledge_allowed": (
                False
            ),
            "evidence_basis": (
                "exact retrieved chunks from "
                "the canonical E2E HTTP run"
            ),
        },
        "provenance": {
            "manifest_path": (
                MANIFEST_PATH.as_posix()
            ),
            "manifest_sha256": (
                sha256_file(
                    MANIFEST_PATH
                )
            ),
            "cases_path": (
                CASES_PATH.as_posix()
            ),
            "cases_git_blob_sha256": (
                manifest[
                    "cases"
                ]["sha256"]
            ),
            "results_path": (
                RESULTS_PATH.as_posix()
            ),
            "results_sha256": (
                frozen_hashes[
                    "results_sha256"
                ]
            ),
            "corpus_path": (
                CORPUS_PATH.as_posix()
            ),
            "corpus_sha256": (
                frozen_hashes[
                    "corpus_sha256"
                ]
            ),
            "review_packet_path": (
                PACKET_PATH.as_posix()
            ),
            "review_packet_sha256": (
                sha256_file(
                    PACKET_PATH
                )
            ),
            "human_scores_path": (
                SCORES_PATH.as_posix()
            ),
            "human_scores_sha256": (
                sha256_file(
                    SCORES_PATH
                )
            ),
            "structural_report_path": (
                STRUCTURAL_REPORT_PATH.as_posix()
            ),
            "structural_report_sha256": (
                sha256_file(
                    STRUCTURAL_REPORT_PATH
                )
            ),
        },
        "validation": (
            validation_summary
        ),
        "overall": {
            **overall,
            "partial_case_ids": (
                partial_case_ids
            ),
            "fail_case_ids": (
                fail_case_ids
            ),
            "blocker_case_ids": (
                blocker_case_ids
            ),
        },
        "semantic_gate": gate,
        "by_category": (
            grouped_breakdown(
                scores,
                "category",
            )
        ),
        "by_expected_behavior": (
            grouped_breakdown(
                scores,
                "expected_behavior",
            )
        ),
        "dimensions": (
            dimension_summary(
                scores
            )
        ),
        "case_verdicts": {
            record["case_id"]: {
                "verdict": (
                    record["verdict"]
                ),
                "blocker": (
                    record["blocker"]
                ),
                "notes": (
                    record["notes"]
                ),
            }
            for record in scores
        },
    }


def write_report(
    report: dict[str, Any],
) -> None:
    REPORT_PATH.parent.mkdir(
        parents=True,
        exist_ok=True,
    )

    REPORT_PATH.write_text(
        json.dumps(
            report,
            indent=2,
            ensure_ascii=False,
        )
        + "\n",
        encoding="utf-8",
    )


def main() -> int:
    report = build_report()

    write_report(
        report
    )

    overall = report[
        "overall"
    ]

    gate = report[
        "semantic_gate"
    ]

    print("=" * 72)
    print(
        "E2E SEMANTIC EVALUATION V1"
    )
    print("=" * 72)

    print(
        "Cases              :",
        overall["case_count"],
    )
    print(
        "Pass               :",
        overall["pass_count"],
    )
    print(
        "Partial            :",
        overall["partial_count"],
    )
    print(
        "Fail               :",
        overall["fail_count"],
    )
    print(
        "Pass rate          :",
        f"{overall['pass_rate']:.1%}",
    )
    print(
        "Pass + Partial     :",
        f"{overall['pass_or_partial_rate']:.1%}",
    )
    print(
        "Blocker case IDs   :",
        overall[
            "blocker_case_ids"
        ],
    )
    print(
        "Semantic gate pass :",
        gate["pass"],
    )

    print()
    print(
        "Results SHA256     :",
        report[
            "provenance"
        ]["results_sha256"],
    )
    print(
        "Corpus SHA256      :",
        report[
            "provenance"
        ]["corpus_sha256"],
    )
    print(
        "Packet SHA256      :",
        report[
            "provenance"
        ]["review_packet_sha256"],
    )
    print(
        "Scores SHA256      :",
        report[
            "provenance"
        ]["human_scores_sha256"],
    )
    print(
        "Report             :",
        REPORT_PATH,
    )

    return (
        0
        if gate["pass"]
        else 1
    )


if __name__ == "__main__":
    raise SystemExit(
        main()
    )
