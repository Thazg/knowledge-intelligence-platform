from __future__ import annotations

from copy import deepcopy

import pytest

from scripts.validate_e2e_human_scores_v1 import (
    validate_verdict_score_consistency,
)


def _record(
    *,
    verdict: str = "pass",
) -> dict:
    return {
        "case_id": "e2e-test",
        "correctness": 2,
        "faithfulness": 2,
        "citation_correctness": 2,
        "citation_completeness": 2,
        "evidence_sufficiency": 2,
        "ambiguity_handling": None,
        "multi_source_synthesis": None,
        "abstention": None,
        "verdict": verdict,
    }


def test_pass_accepts_all_applicable_scores_of_two() -> None:
    record = _record(
        verdict="pass"
    )

    validate_verdict_score_consistency(
        record
    )


def test_pass_rejects_partial_score() -> None:
    record = _record(
        verdict="pass"
    )
    record["faithfulness"] = 1

    with pytest.raises(
        ValueError,
        match="PASS requires",
    ):
        validate_verdict_score_consistency(
            record
        )


def test_partial_requires_at_least_one_score_of_one() -> None:
    record = _record(
        verdict="partial"
    )

    with pytest.raises(
        ValueError,
        match="PARTIAL requires",
    ):
        validate_verdict_score_consistency(
            record
        )


def test_partial_accepts_one_without_zero() -> None:
    record = _record(
        verdict="partial"
    )
    record["evidence_sufficiency"] = 1

    validate_verdict_score_consistency(
        record
    )


def test_partial_rejects_zero() -> None:
    record = _record(
        verdict="partial"
    )
    record["correctness"] = 0
    record["faithfulness"] = 1

    with pytest.raises(
        ValueError,
        match="PARTIAL cannot contain",
    ):
        validate_verdict_score_consistency(
            record
        )


def test_fail_requires_zero() -> None:
    record = _record(
        verdict="fail"
    )
    record["correctness"] = 1

    with pytest.raises(
        ValueError,
        match="FAIL requires",
    ):
        validate_verdict_score_consistency(
            record
        )


def test_fail_accepts_zero_score() -> None:
    record = _record(
        verdict="fail"
    )
    record["ambiguity_handling"] = 0

    validate_verdict_score_consistency(
        record
    )


def test_null_optional_dimensions_are_ignored() -> None:
    record = deepcopy(
        _record(verdict="pass")
    )

    assert (
        record["ambiguity_handling"]
        is None
    )
    assert (
        record["multi_source_synthesis"]
        is None
    )
    assert record["abstention"] is None

    validate_verdict_score_consistency(
        record
    )
