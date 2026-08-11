from __future__ import annotations

import argparse
import json
from pathlib import Path

from backend.evaluation.generation_evaluator import (
    evaluate_generation_records,
)
from backend.evaluation.generation_regression import (
    check_generation_regression,
)


DEFAULT_CASES_PATH = Path(
    "benchmarks/generation/cases_v1.jsonl"
)

DEFAULT_MANIFEST_PATH = Path(
    "benchmarks/generation/v1/manifest.json"
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
                    f"Invalid JSON at line "
                    f"{line_number} in {path}: {exc}"
                ) from exc

            records.append(record)

    return records


def main(
    cases_path: Path,
    results_path: Path,
    manifest_path: Path,
) -> int:
    cases = load_jsonl(cases_path)
    results = load_jsonl(results_path)

    manifest = json.loads(
        manifest_path.read_text(
            encoding="utf-8"
        )
    )

    evaluation = evaluate_generation_records(
        cases=cases,
        results=results,
    )

    regression = check_generation_regression(
        evaluation=evaluation,
        manifest=manifest,
    )

    print(
        json.dumps(
            {
                "evaluation": {
                    "case_integrity": evaluation[
                        "case_integrity"
                    ],
                    "execution": evaluation[
                        "execution"
                    ],
                    "citations": evaluation[
                        "citations"
                    ],
                    "evidence": evaluation[
                        "evidence"
                    ],
                    "result_integrity": evaluation[
                        "result_integrity"
                    ],
                },
                "regression": regression,
            },
            indent=2,
        )
    )

    return 0 if regression["passed"] else 1


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description=(
            "Check generation benchmark results "
            "against the approved regression policy."
        )
    )

    parser.add_argument(
        "--cases",
        type=Path,
        default=DEFAULT_CASES_PATH,
        help="Generation benchmark cases JSONL.",
    )

    parser.add_argument(
        "--results",
        type=Path,
        required=True,
        help="Generation benchmark results JSONL.",
    )

    parser.add_argument(
        "--manifest",
        type=Path,
        default=DEFAULT_MANIFEST_PATH,
        help="Generation benchmark manifest JSON.",
    )

    return parser.parse_args()


if __name__ == "__main__":
    args = parse_args()

    raise SystemExit(
        main(
            cases_path=args.cases,
            results_path=args.results,
            manifest_path=args.manifest,
        )
    )