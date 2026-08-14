from __future__ import annotations

from scripts.evaluate_e2e_semantic_v1 import (
    dimension_summary,
    grouped_breakdown,
    semantic_gate,
    verdict_summary,
)


def _record(
    case_id: str,
    *,
    verdict: str,
    blocker: bool = False,
    category: str = "semantic",
    behavior: str = "answer_with_evidence",
    correctness: int = 2,
    ambiguity: int | None = None,
) -> dict:
    return {
        "case_id": case_id,
        "category": category,
        "expected_behavior": behavior,
        "correctness": correctness,
        "faithfulness": 2,
        "citation_correctness": 2,
        "citation_completeness": 2,
        "evidence_sufficiency": 2,
        "ambiguity_handling": ambiguity,
        "multi_source_synthesis": None,
        "abstention": None,
        "verdict": verdict,
        "blocker": blocker,
        "notes": "reviewed",
    }


def test_verdict_summary_counts_and_rates() -> None:
    records = [
        _record(
            "a",
            verdict="pass",
        ),
        _record(
            "b",
            verdict="partial",
        ),
        _record(
            "c",
            verdict="fail",
        ),
    ]

    summary = verdict_summary(
        records
    )

    assert summary["case_count"] == 3
    assert summary["pass_count"] == 1
    assert summary["partial_count"] == 1
    assert summary["fail_count"] == 1
    assert summary["pass_rate"] == 0.3333
    assert (
        summary["pass_or_partial_rate"]
        == 0.6667
    )


def test_semantic_gate_passes_clean_set() -> None:
    records = [
        _record(
            "a",
            verdict="pass",
        ),
        _record(
            "b",
            verdict="partial",
        ),
    ]

    gate = semantic_gate(
        records
    )

    assert gate["pass"] is True
    assert gate["fail_case_ids"] == []
    assert gate["blocker_case_ids"] == []


def test_semantic_gate_fails_on_fail() -> None:
    records = [
        _record(
            "a",
            verdict="fail",
        )
    ]

    gate = semantic_gate(
        records
    )

    assert gate["pass"] is False
    assert gate["fail_case_ids"] == [
        "a"
    ]


def test_semantic_gate_fails_on_blocker() -> None:
    records = [
        _record(
            "a",
            verdict="partial",
            blocker=True,
        )
    ]

    gate = semantic_gate(
        records
    )

    assert gate["pass"] is False
    assert gate[
        "blocker_case_ids"
    ] == ["a"]


def test_dimension_summary_ignores_null() -> None:
    records = [
        _record(
            "a",
            verdict="pass",
            correctness=2,
            ambiguity=None,
        ),
        _record(
            "b",
            verdict="partial",
            correctness=1,
            ambiguity=1,
        ),
    ]

    summary = dimension_summary(
        records
    )

    assert (
        summary["correctness"][
            "applicable_case_count"
        ]
        == 2
    )
    assert (
        summary["correctness"][
            "mean_score"
        ]
        == 1.5
    )

    assert (
        summary[
            "ambiguity_handling"
        ][
            "applicable_case_count"
        ]
        == 1
    )

    assert (
        summary[
            "ambiguity_handling"
        ]["mean_score"]
        == 1
    )


def test_grouped_breakdown_tracks_groups() -> None:
    records = [
        _record(
            "a",
            verdict="pass",
            category="semantic",
        ),
        _record(
            "b",
            verdict="partial",
            category="semantic",
        ),
        _record(
            "c",
            verdict="pass",
            category="lexical",
        ),
    ]

    breakdown = grouped_breakdown(
        records,
        "category",
    )

    assert (
        breakdown["semantic"][
            "case_count"
        ]
        == 2
    )

    assert (
        breakdown["semantic"][
            "pass_count"
        ]
        == 1
    )

    assert (
        breakdown["semantic"][
            "partial_count"
        ]
        == 1
    )

    assert (
        breakdown["lexical"][
            "pass_count"
        ]
        == 1
    )
