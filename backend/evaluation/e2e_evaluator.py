from __future__ import annotations

from collections import Counter
from typing import Any

from backend.evaluation.generation_evaluator import (
    evaluate_generation_records,
)


TIMING_FIELDS = (
    "http_round_trip_latency_ms",
    "retrieval_latency_ms",
    "context_build_latency_ms",
    "generation_latency_ms",
    "end_to_end_latency_ms",
)

RESPONSE_FIELDS = {
    "query": str,
    "answer": str,
    "citations": list,
    "sources": list,
    "model": str,
    "metrics": dict,
}

IDENTITY_FIELDS = (
    "citation_id",
    "document_id",
    "chunk_id",
)


def _is_non_negative_number(value: Any) -> bool:
    return (
        isinstance(value, (int, float))
        and not isinstance(value, bool)
        and value >= 0
    )


def _is_non_empty_string(value: Any) -> bool:
    return (
        isinstance(value, str)
        and bool(value.strip())
    )


def _response_schema_errors(
    result: dict,
) -> list[str]:
    payload = result.get("response_json")

    if not isinstance(payload, dict):
        return ["response_json_not_object"]

    errors: list[str] = []

    for field, expected_type in (
        RESPONSE_FIELDS.items()
    ):
        value = payload.get(field)

        if not isinstance(
            value,
            expected_type,
        ):
            errors.append(
                f"response_json.{field}_invalid_type"
            )

    return errors


def _source_metadata_errors(
    sources: Any,
) -> list[dict]:
    if not isinstance(sources, list):
        return [
            {
                "index": None,
                "errors": ["sources_not_list"],
            }
        ]

    issues: list[dict] = []

    for index, source in enumerate(sources):
        errors: list[str] = []

        if not isinstance(source, dict):
            issues.append(
                {
                    "index": index,
                    "errors": ["source_not_object"],
                }
            )
            continue

        for field in IDENTITY_FIELDS:
            if not _is_non_empty_string(
                source.get(field)
            ):
                errors.append(
                    f"{field}_missing_or_empty"
                )

        for optional_field in (
            "title",
            "source",
            "url",
        ):
            value = source.get(
                optional_field
            )

            if (
                value is not None
                and not isinstance(value, str)
            ):
                errors.append(
                    f"{optional_field}_invalid_type"
                )

        if errors:
            issues.append(
                {
                    "index": index,
                    "citation_id": source.get(
                        "citation_id"
                    ),
                    "errors": errors,
                }
            )

    return issues


def _citation_metadata_errors(
    citations: Any,
) -> list[dict]:
    if not isinstance(citations, list):
        return [
            {
                "index": None,
                "errors": ["citations_not_list"],
            }
        ]

    issues: list[dict] = []

    for index, citation in enumerate(
        citations
    ):
        errors: list[str] = []

        if not isinstance(citation, dict):
            issues.append(
                {
                    "index": index,
                    "errors": [
                        "citation_not_object"
                    ],
                }
            )
            continue

        for field in IDENTITY_FIELDS:
            if not _is_non_empty_string(
                citation.get(field)
            ):
                errors.append(
                    f"{field}_missing_or_empty"
                )

        if errors:
            issues.append(
                {
                    "index": index,
                    "citation_id": citation.get(
                        "citation_id"
                    ),
                    "errors": errors,
                }
            )

    return issues


def _orphan_api_citation_ids(
    result: dict,
) -> list[str]:
    sources = result.get("sources", [])
    citations = result.get("citations", [])

    if not isinstance(sources, list):
        return []

    if not isinstance(citations, list):
        return []

    source_ids = {
        str(source.get("citation_id"))
        for source in sources
        if isinstance(source, dict)
        and source.get("citation_id")
        is not None
    }

    return sorted(
        {
            str(citation.get("citation_id"))
            for citation in citations
            if isinstance(citation, dict)
            and citation.get("citation_id")
            is not None
            and str(
                citation.get("citation_id")
            )
            not in source_ids
        }
    )


def _timing_errors(
    result: dict,
) -> list[str]:
    return [
        field
        for field in TIMING_FIELDS
        if not _is_non_negative_number(
            result.get(field)
        )
    ]


def evaluate_e2e_records(
    cases: list[dict],
    results: list[dict],
    *,
    expected_model: str,
) -> dict:
    generation_report = (
        evaluate_generation_records(
            cases,
            results,
        )
    )

    expected_case_ids = {
        case["case_id"]
        for case in cases
    }

    case_by_id = {
        case["case_id"]: case
        for case in cases
    }

    result_case_counts = Counter(
        result["case_id"]
        for result in results
    )

    per_case: dict[str, dict] = {}
    failing_case_ids: set[str] = set()

    for result in results:
        case_id = result["case_id"]

        if case_id not in expected_case_ids:
            continue

        hard_gate_failures: list[str] = []

        runtime_error = result.get("error")

        if runtime_error is not None:
            hard_gate_failures.append(
                "runtime_error"
            )

        if result.get("http_status") != 200:
            hard_gate_failures.append(
                "unexpected_http_status"
            )

        request_id_sent = result.get(
            "request_id_sent"
        )
        request_id_received = result.get(
            "request_id_received"
        )

        if (
            not _is_non_empty_string(
                request_id_sent
            )
            or request_id_sent
            != request_id_received
        ):
            hard_gate_failures.append(
                "request_id_mismatch"
            )

        if not _is_non_empty_string(
            result.get("answer")
        ):
            hard_gate_failures.append(
                "empty_answer"
            )

        if (
            result.get("model")
            != expected_model
        ):
            hard_gate_failures.append(
                "unexpected_model"
            )

        schema_errors: list[str] = []
        source_metadata_errors: list[
            dict
        ] = []
        citation_metadata_errors: list[
            dict
        ] = []

        if runtime_error is None:
            schema_errors = (
                _response_schema_errors(
                    result
                )
            )

            source_metadata_errors = (
                _source_metadata_errors(
                    result.get("sources")
                )
            )

            citation_metadata_errors = (
                _citation_metadata_errors(
                    result.get("citations")
                )
            )

            if schema_errors:
                hard_gate_failures.append(
                    "invalid_response_schema"
                )

            if source_metadata_errors:
                hard_gate_failures.append(
                    "invalid_source_metadata"
                )

            if citation_metadata_errors:
                hard_gate_failures.append(
                    "invalid_citation_metadata"
                )

        timing_errors = _timing_errors(
            result
        )

        if timing_errors:
            hard_gate_failures.append(
                "missing_or_negative_timing"
            )

        generation_case = (
            generation_report["per_case"].get(
                case_id,
                {},
            )
        )

        invalid_citation_ids = (
            generation_case.get(
                "invalid_citation_ids",
                [],
            )
        )

        mapping_errors = (
            generation_case.get(
                "citation_source_mapping_errors",
                [],
            )
        )

        duplicate_source_ids = (
            generation_case.get(
                "duplicate_source_citation_ids",
                [],
            )
        )

        orphan_api_citation_ids = (
            _orphan_api_citation_ids(
                result
            )
        )

        if invalid_citation_ids:
            hard_gate_failures.append(
                "invalid_raw_citation_id"
            )

        if (
            mapping_errors
            or orphan_api_citation_ids
        ):
            hard_gate_failures.append(
                "citation_source_mapping_error"
            )

        if duplicate_source_ids:
            hard_gate_failures.append(
                "duplicate_source_citation_id"
            )

        expected_behavior = (
            case_by_id[case_id].get(
                "expected_behavior"
            )
        )

        valid_citation_ids = (
            generation_case.get(
                "valid_citation_ids",
                [],
            )
        )

        if (
            expected_behavior
            == "answer_with_evidence"
            and not valid_citation_ids
        ):
            hard_gate_failures.append(
                "missing_required_evidence"
            )

        hard_gate_failures = list(
            dict.fromkeys(
                hard_gate_failures
            )
        )

        if hard_gate_failures:
            failing_case_ids.add(
                case_id
            )

        per_case[case_id] = {
            "hard_gate_pass": (
                not hard_gate_failures
            ),
            "hard_gate_failures": (
                hard_gate_failures
            ),
            "schema_errors": schema_errors,
            "timing_errors": timing_errors,
            "source_metadata_errors": (
                source_metadata_errors
            ),
            "citation_metadata_errors": (
                citation_metadata_errors
            ),
            "orphan_api_citation_ids": (
                orphan_api_citation_ids
            ),
            **generation_case,
        }

    global_hard_gate_failures: list[
        str
    ] = []

    case_integrity = generation_report[
        "case_integrity"
    ]

    if case_integrity["missing_case_ids"]:
        global_hard_gate_failures.append(
            "missing_cases"
        )

    if case_integrity["duplicate_case_ids"]:
        global_hard_gate_failures.append(
            "duplicate_cases"
        )

    if case_integrity["unknown_case_ids"]:
        global_hard_gate_failures.append(
            "unknown_cases"
        )

    duplicated_expected_results = sorted(
        case_id
        for case_id, count
        in result_case_counts.items()
        if case_id in expected_case_ids
        and count > 1
    )

    structural_pass = (
        not global_hard_gate_failures
        and not failing_case_ids
    )

    return {
        "structural_pass": structural_pass,
        "expected_model": expected_model,
        "summary": {
            "expected_case_count": len(
                cases
            ),
            "result_record_count": len(
                results
            ),
            "structural_pass_case_count": (
                len(expected_case_ids)
                - len(failing_case_ids)
                - len(
                    case_integrity[
                        "missing_case_ids"
                    ]
                )
            ),
            "structural_fail_case_count": (
                len(failing_case_ids)
            ),
            "structural_fail_case_ids": (
                sorted(failing_case_ids)
            ),
            "global_hard_gate_failures": (
                global_hard_gate_failures
            ),
        },
        "case_integrity": {
            **case_integrity,
            "duplicated_expected_result_case_ids": (
                duplicated_expected_results
            ),
        },
        "execution": generation_report[
            "execution"
        ],
        "citations": generation_report[
            "citations"
        ],
        "evidence": generation_report[
            "evidence"
        ],
        "result_integrity": (
            generation_report[
                "result_integrity"
            ]
        ),
        "per_case": per_case,
    }
