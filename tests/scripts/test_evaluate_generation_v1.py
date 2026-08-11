from __future__ import annotations

import sys
from pathlib import Path

from scripts.evaluate_generation_v1 import (
    DEFAULT_OUTPUT_PATH,
    parse_args,
)


def test_parse_args_uses_default_generation_output(
    monkeypatch,
) -> None:
    monkeypatch.setattr(
        sys,
        "argv",
        ["evaluate_generation_v1.py"],
    )

    args = parse_args()

    assert args.output == DEFAULT_OUTPUT_PATH


def test_parse_args_accepts_custom_generation_output(
    monkeypatch,
) -> None:
    output_path = Path(
        "benchmarks/generation/repeatability/run_01.jsonl"
    )

    monkeypatch.setattr(
        sys,
        "argv",
        [
            "evaluate_generation_v1.py",
            "--output",
            str(output_path),
        ],
    )

    args = parse_args()

    assert args.output == output_path