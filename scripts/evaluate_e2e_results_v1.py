from __future__ import annotations

import argparse
import hashlib
import json
import subprocess
from pathlib import Path
from typing import Any

from backend.evaluation.e2e_evaluator import (
    evaluate_e2e_records,
)


DEFAULT_MANIFEST_PATH = Path(
    "benchmarks/e2e/v1/manifest.json"
)

DEFAULT_RESULTS_PATH = Path(
    "benchmarks/e2e/results_v1.jsonl"
)

DEFAULT_REPORT_PATH = Path(
    "benchmarks/e2e/reports/e2e_structural_v1.json"
)


def load_json(path: Path) -> dict:
    return json.loads(
        path.read_text(encoding="utf-8")
    )


def load_jsonl(path: Path) -> list[dict]:
    records: list[dict] = []

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
                    f"Invalid JSON at "
                    f"{path}:{line_number}: {exc}"
                ) from exc

            records.append(record)

    return records


def sha256_bytes(data: bytes) -> str:
    return hashlib.sha256(
        data
    ).hexdigest().upper()


def sha256_file(path: Path) -> str:
    return sha256_bytes(
        path.read_bytes()
    )


def git_blob_sha256(path: str) -> str:
    blob = subprocess.check_output(
        ["git", "show", f"HEAD:{path}"]
    )

    return sha256_bytes(blob)


def build_structural_report(
    *,
    manifest_path: Path,
    results_path: Path,
) -> dict[str, Any]:
    manifest = load_json(
        manifest_path
    )

    cases_path = Path(
        manifest["cases"]["path"]
    )

    cases = load_jsonl(
        cases_path
    )

    results = load_jsonl(
        results_path
    )

    observed_cases_git_sha = (
        git_blob_sha256(
            manifest["cases"]["path"]
        )
    )

    expected_cases_sha = (
        manifest["cases"]["sha256"]
    )

    if (
        observed_cases_git_sha
        != expected_cases_sha
    ):
        raise RuntimeError(
            "Canonical cases no longer "
            "match the frozen manifest: "
            f"expected={expected_cases_sha}, "
            f"observed={observed_cases_git_sha}"
        )

    expected_model = manifest[
        "generator"
    ]["model"]

    evaluation = evaluate_e2e_records(
        cases,
        results,
        expected_model=expected_model,
    )

    return {
        "report_version": (
            "e2e_structural_v1"
        ),
        "benchmark_version": manifest[
            "benchmark_version"
        ],
        "inputs": {
            "manifest_path": str(
                manifest_path
            ).replace("\\", "/"),
            "manifest_sha256": (
                sha256_file(
                    manifest_path
                )
            ),
            "cases_path": str(
                cases_path
            ).replace("\\", "/"),
            "cases_git_blob_sha256": (
                observed_cases_git_sha
            ),
            "results_path": str(
                results_path
            ).replace("\\", "/"),
            "results_sha256": (
                sha256_file(
                    results_path
                )
            ),
        },
        "runtime_provenance": {
            "api_source_git_commit": (
                manifest[
                    "source_control"
                ]["git_commit"]
            ),
            "benchmark_runner_git_commit": (
                manifest[
                    "benchmark_runner"
                ]["git_commit"]
            ),
            "benchmark_runner_sha256": (
                manifest[
                    "benchmark_runner"
                ]["source_sha256"]
            ),
            "api_image_id": (
                manifest[
                    "deployment"
                ]["api_image"]["image_id"]
            ),
            "ollama_version": (
                manifest[
                    "generator"
                ]["ollama_version"]
            ),
            "model": expected_model,
            "model_digest": (
                manifest[
                    "generator"
                ]["model_digest"]
            ),
            "docker_total_memory_gib": (
                manifest[
                    "runtime_environment"
                ][
                    "docker_total_memory_gib_observed"
                ]
            ),
        },
        "evaluation": evaluation,
    }


def write_report(
    path: Path,
    report: dict,
) -> None:
    path.parent.mkdir(
        parents=True,
        exist_ok=True,
    )

    path.write_text(
        json.dumps(
            report,
            indent=2,
            ensure_ascii=False,
        )
        + "\n",
        encoding="utf-8",
    )


def main(
    *,
    manifest_path: Path,
    results_path: Path,
    report_path: Path,
) -> int:
    report = build_structural_report(
        manifest_path=manifest_path,
        results_path=results_path,
    )

    write_report(
        report_path,
        report,
    )

    evaluation = report[
        "evaluation"
    ]

    summary = evaluation[
        "summary"
    ]

    print("=" * 72)
    print(
        "E2E V1 STRUCTURAL EVALUATION"
    )
    print("=" * 72)

    print(
        "Structural pass     :",
        evaluation["structural_pass"],
    )

    print(
        "Expected cases      :",
        summary["expected_case_count"],
    )

    print(
        "Result records      :",
        summary["result_record_count"],
    )

    print(
        "Passing cases       :",
        summary[
            "structural_pass_case_count"
        ],
    )

    print(
        "Failing cases       :",
        summary[
            "structural_fail_case_count"
        ],
    )

    print(
        "Failing case IDs    :",
        summary[
            "structural_fail_case_ids"
        ],
    )

    print(
        "Global failures     :",
        summary[
            "global_hard_gate_failures"
        ],
    )

    print()
    print(
        "Raw citations       :",
        evaluation[
            "citations"
        ][
            "total_raw_citation_count"
        ],
    )

    print(
        "Valid citations     :",
        evaluation[
            "citations"
        ][
            "total_valid_citation_count"
        ],
    )

    print(
        "Invalid citations   :",
        evaluation[
            "citations"
        ][
            "total_invalid_citation_count"
        ],
    )

    print(
        "Missing evidence    :",
        evaluation[
            "evidence"
        ][
            "missing_evidence_case_count"
        ],
    )

    print(
        "Mapping errors      :",
        evaluation[
            "result_integrity"
        ][
            "citation_source_mapping_error_count"
        ],
    )

    print(
        "Duplicate source IDs:",
        evaluation[
            "result_integrity"
        ][
            "duplicate_source_citation_id_count"
        ],
    )

    print()
    print(
        "Results SHA256      :",
        report["inputs"][
            "results_sha256"
        ],
    )

    print(
        "Report              :",
        report_path,
    )

    return (
        0
        if evaluation[
            "structural_pass"
        ]
        else 1
    )


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description=(
            "Evaluate canonical E2E v1 "
            "HTTP results against deterministic "
            "structural hard gates."
        )
    )

    parser.add_argument(
        "--manifest",
        type=Path,
        default=DEFAULT_MANIFEST_PATH,
    )

    parser.add_argument(
        "--results",
        type=Path,
        default=DEFAULT_RESULTS_PATH,
    )

    parser.add_argument(
        "--report",
        type=Path,
        default=DEFAULT_REPORT_PATH,
    )

    return parser.parse_args()


if __name__ == "__main__":
    args = parse_args()

    raise SystemExit(
        main(
            manifest_path=args.manifest,
            results_path=args.results,
            report_path=args.report,
        )
    )
