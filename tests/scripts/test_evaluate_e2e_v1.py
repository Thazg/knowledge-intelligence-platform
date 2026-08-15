from __future__ import annotations

import json

import pytest

from scripts.evaluate_e2e_v1 import (
    build_success_record,
    load_cases,
    request_id_for_case,
    validate_readiness_payload,
)


def test_load_cases_reads_jsonl_and_skips_blank_lines(
    tmp_path,
) -> None:
    path = tmp_path / "cases.jsonl"

    path.write_text(
        "\n".join(
            [
                json.dumps(
                    {
                        "case_id": "e2e-001",
                        "query": "Question 1",
                    }
                ),
                "",
                json.dumps(
                    {
                        "case_id": "e2e-002",
                        "query": "Question 2",
                    }
                ),
            ]
        ),
        encoding="utf-8",
    )

    cases = load_cases(path)

    assert [
        case["case_id"]
        for case in cases
    ] == [
        "e2e-001",
        "e2e-002",
    ]


def test_load_cases_reports_invalid_json_line(
    tmp_path,
) -> None:
    path = tmp_path / "cases.jsonl"

    path.write_text(
        '{"case_id":"ok"}\n'
        '{"broken":\n',
        encoding="utf-8",
    )

    with pytest.raises(
        ValueError,
        match="Invalid JSON at line 2",
    ):
        load_cases(path)


def test_build_success_record_preserves_api_and_http_data() -> None:
    case = {
        "case_id": "e2e-001",
        "category": "semantic",
        "query": "Example?",
        "expected_behavior": (
            "answer_with_evidence"
        ),
        "tags": ["single_source"],
        "notes": "Example notes",
    }

    payload = {
        "query": "Example?",
        "answer": "Answer [1].",
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
                "title": "Doc",
                "source": "example",
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

    record = build_success_record(
        case=case,
        status_code=200,
        request_id_sent="sent-id",
        request_id_received="sent-id",
        http_round_trip_latency_ms=35.0,
        payload=payload,
    )

    assert record["http_status"] == 200
    assert (
        record["request_id_sent"]
        == record["request_id_received"]
    )
    assert record["answer"] == "Answer [1]."
    assert record["model"] == "qwen3:4b-instruct"

    assert (
        record["retrieval_latency_ms"]
        == 10.0
    )
    assert (
        record["context_build_latency_ms"]
        == 1.0
    )
    assert (
        record["generation_latency_ms"]
        == 20.0
    )
    assert (
        record["end_to_end_latency_ms"]
        == 31.0
    )
    assert (
        record["http_round_trip_latency_ms"]
        == 35.0
    )

    assert record["response_json"] == payload


def test_validate_readiness_payload_accepts_ready_stack() -> None:
    validate_readiness_payload(
        {
            "status": "ready",
            "dependencies": {
                "rag_service": "ready",
                "qdrant": "ready",
                "ollama": "ready",
            },
        }
    )


def test_validate_readiness_payload_rejects_dependency_failure() -> None:
    with pytest.raises(
        RuntimeError,
        match="qdrant",
    ):
        validate_readiness_payload(
            {
                "status": "ready",
                "dependencies": {
                    "rag_service": "ready",
                    "qdrant": "unavailable",
                    "ollama": "ready",
                },
            }
        )


def test_request_id_is_stable_and_case_specific() -> None:
    assert request_id_for_case(
        "e2e_v1",
        "e2e-014",
    ) == "e2e_v1-e2e-014"
