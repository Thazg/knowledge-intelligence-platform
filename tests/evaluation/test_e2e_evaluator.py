from __future__ import annotations

from copy import deepcopy

from backend.evaluation.e2e_evaluator import (
    evaluate_e2e_records,
)


def _case(
    *,
    case_id: str = "e2e-001",
    expected_behavior: str = (
        "answer_with_evidence"
    ),
) -> dict:
    return {
        "case_id": case_id,
        "category": "semantic",
        "query": "Question?",
        "expected_behavior": (
            expected_behavior
        ),
    }


def _result(
    *,
    case_id: str = "e2e-001",
) -> dict:
    payload = {
        "query": "Question?",
        "answer": "Supported answer [1].",
        "citations": [
            {
                "citation_id": "1",
                "document_id": "doc-1",
                "chunk_id": "chunk-1",
            }
        ],
        "sources": [
            {
                "citation_id": "1",
                "document_id": "doc-1",
                "chunk_id": "chunk-1",
                "title": "Document",
                "source": "docs",
                "url": None,
            }
        ],
        "model": "qwen3:4b-instruct",
        "metrics": {
            "retrieval_latency_ms": 10.0,
            "context_build_latency_ms": 1.0,
            "generation_latency_ms": 20.0,
            "end_to_end_latency_ms": 31.0,
        },
    }

    return {
        "case_id": case_id,
        "category": "semantic",
        "query": "Question?",
        "expected_behavior": (
            "answer_with_evidence"
        ),
        "http_status": 200,
        "request_id_sent": (
            f"e2e_v1-{case_id}"
        ),
        "request_id_received": (
            f"e2e_v1-{case_id}"
        ),
        "http_round_trip_latency_ms": (
            35.0
        ),
        "answer": payload["answer"],
        "citations": payload[
            "citations"
        ],
        "sources": payload["sources"],
        "model": payload["model"],
        "retrieval_latency_ms": 10.0,
        "context_build_latency_ms": 1.0,
        "generation_latency_ms": 20.0,
        "end_to_end_latency_ms": 31.0,
        "response_json": payload,
    }


def _evaluate(
    case: dict,
    result: dict,
) -> dict:
    return evaluate_e2e_records(
        [case],
        [result],
        expected_model=(
            "qwen3:4b-instruct"
        ),
    )


def test_accepts_structurally_valid_record() -> None:
    report = _evaluate(
        _case(),
        _result(),
    )

    assert (
        report["structural_pass"]
        is True
    )
    assert (
        report["summary"][
            "structural_fail_case_count"
        ]
        == 0
    )


def test_detects_raw_invalid_citation_even_if_api_omits_it() -> None:
    result = _result()

    result["answer"] = (
        "Unsupported citation [9]."
    )
    result["response_json"][
        "answer"
    ] = result["answer"]

    result["citations"] = []
    result["response_json"][
        "citations"
    ] = []

    report = _evaluate(
        _case(),
        result,
    )

    case_report = report[
        "per_case"
    ]["e2e-001"]

    assert (
        case_report[
            "invalid_citation_ids"
        ]
        == ["9"]
    )

    assert (
        "invalid_raw_citation_id"
        in case_report[
            "hard_gate_failures"
        ]
    )


def test_detects_citation_source_mapping_mismatch() -> None:
    result = _result()

    result["citations"][0][
        "document_id"
    ] = "wrong-doc"

    report = _evaluate(
        _case(),
        result,
    )

    assert (
        "citation_source_mapping_error"
        in report["per_case"][
            "e2e-001"
        ]["hard_gate_failures"]
    )


def test_detects_duplicate_source_citation_ids() -> None:
    result = _result()

    duplicate = deepcopy(
        result["sources"][0]
    )
    duplicate["document_id"] = (
        "doc-2"
    )
    duplicate["chunk_id"] = (
        "chunk-2"
    )

    result["sources"].append(
        duplicate
    )

    report = _evaluate(
        _case(),
        result,
    )

    case_report = report[
        "per_case"
    ]["e2e-001"]

    assert (
        case_report[
            "duplicate_source_citation_ids"
        ]
        == ["1"]
    )

    assert (
        "duplicate_source_citation_id"
        in case_report[
            "hard_gate_failures"
        ]
    )


def test_requires_evidence_for_evidence_case() -> None:
    result = _result()

    result["answer"] = (
        "Answer without citation."
    )
    result["response_json"][
        "answer"
    ] = result["answer"]

    result["citations"] = []
    result["response_json"][
        "citations"
    ] = []

    report = _evaluate(
        _case(),
        result,
    )

    assert (
        "missing_required_evidence"
        in report["per_case"][
            "e2e-001"
        ]["hard_gate_failures"]
    )


def test_detects_request_id_model_and_timing_failures() -> None:
    result = _result()

    result[
        "request_id_received"
    ] = "different"

    result["model"] = "wrong-model"
    result["response_json"][
        "model"
    ] = "wrong-model"

    result[
        "generation_latency_ms"
    ] = -1.0

    report = _evaluate(
        _case(),
        result,
    )

    case_report = report[
        "per_case"
    ]["e2e-001"]

    assert (
        "request_id_mismatch"
        in case_report[
            "hard_gate_failures"
        ]
    )

    assert (
        "unexpected_model"
        in case_report[
            "hard_gate_failures"
        ]
    )

    assert (
        "missing_or_negative_timing"
        in case_report[
            "hard_gate_failures"
        ]
    )


def test_detects_invalid_source_metadata() -> None:
    result = _result()

    result["sources"][0][
        "document_id"
    ] = ""

    report = _evaluate(
        _case(),
        result,
    )

    assert (
        "invalid_source_metadata"
        in report["per_case"][
            "e2e-001"
        ]["hard_gate_failures"]
    )


def test_reports_runtime_error_and_non_200() -> None:
    result = {
        "case_id": "e2e-001",
        "category": "semantic",
        "query": "Question?",
        "expected_behavior": (
            "answer_with_evidence"
        ),
        "error": "ReadTimeout",
        "message": "timed out",
        "http_status": None,
        "request_id_sent": (
            "e2e_v1-e2e-001"
        ),
        "request_id_received": None,
        "http_round_trip_latency_ms": (
            150000.0
        ),
    }

    report = _evaluate(
        _case(),
        result,
    )

    failures = report[
        "per_case"
    ]["e2e-001"][
        "hard_gate_failures"
    ]

    assert "runtime_error" in failures
    assert (
        "unexpected_http_status"
        in failures
    )
