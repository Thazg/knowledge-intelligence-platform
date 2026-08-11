from __future__ import annotations

import re
from collections import Counter


def evaluate_generation_records(
    cases: list[dict],
    results: list[dict],
) -> dict:
    expected_case_ids = [
        case["case_id"]
        for case in cases
    ]

    result_case_ids = [
        result["case_id"]
        for result in results
    ]

    expected_case_id_set = set(expected_case_ids)
    result_case_id_set = set(result_case_ids)

    result_case_counts = Counter(result_case_ids)

    missing_case_ids = sorted(
        expected_case_id_set - result_case_id_set
    )

    duplicate_case_ids = sorted(
        case_id
        for case_id, count in result_case_counts.items()
        if count > 1
    )

    unknown_case_ids = sorted(
        result_case_id_set - expected_case_id_set
    )

    generation_failure_case_ids = sorted(
        result["case_id"]
        for result in results
        if "error" in result
    )

    empty_answer_case_ids = sorted(
        result["case_id"]
        for result in results
        if "error" not in result
        and not str(result.get("answer", "")).strip()
    )

    expected_behavior_by_case_id = {
        case["case_id"]: case.get("expected_behavior")
        for case in cases
    }

    answer_with_evidence_case_ids = sorted(
        case_id
        for case_id, expected_behavior
        in expected_behavior_by_case_id.items()
        if expected_behavior == "answer_with_evidence"
    )

    total_raw_citation_count = 0
    total_valid_citation_count = 0
    total_invalid_citation_count = 0

    total_citation_format_violation_count = 0
    citation_format_violation_case_ids: list[str] = []

    invalid_citation_case_ids: list[str] = []

    citation_source_mapping_error_count = 0
    citation_source_mapping_error_case_ids: list[str] = []
    
    duplicate_source_citation_id_count = 0
    duplicate_source_citation_id_case_ids: list[str] = []

    per_case: dict[str, dict] = {}

    for result in results:
        case_id = result["case_id"]

        if "error" in result:
            continue

        answer = str(result.get("answer", ""))

        sources = result.get("sources", [])

        source_citation_ids = [
            str(source["citation_id"])
            for source in sources
        ]

        source_citation_id_counts = Counter(
            source_citation_ids
        )

        duplicate_source_citation_ids = sorted(
            citation_id
            for citation_id, count
            in source_citation_id_counts.items()
            if count > 1
        )

        duplicate_source_citation_id_count += len(
            duplicate_source_citation_ids
        )

        if duplicate_source_citation_ids:
            duplicate_source_citation_id_case_ids.append(
                case_id
            )

        source_by_citation_id = {
            str(source["citation_id"]): source
            for source in sources
        }

        available_source_ids = set(
            source_by_citation_id
        )

        raw_citation_ids = re.findall(
            r"\[(?:SOURCE\s+)?(\d+)\]",
            answer,
            flags=re.IGNORECASE,
        )

        citation_format_violations = re.findall(
            r"\[SOURCE\s+\d+\]",
            answer,
            flags=re.IGNORECASE,
        )

        valid_citation_ids = [
            citation_id
            for citation_id in raw_citation_ids
            if citation_id in available_source_ids
        ]

        invalid_citation_ids = [
            citation_id
            for citation_id in raw_citation_ids
            if citation_id not in available_source_ids
        ]

        citation_source_mapping_errors: list[dict] = []

        for citation in result.get("citations", []):
            citation_id = str(
                citation["citation_id"]
            )

            source = source_by_citation_id.get(
                citation_id
            )

            if source is None:
                continue

            expected_document_id = source.get(
                "document_id"
            )
            expected_chunk_id = source.get(
                "chunk_id"
            )

            actual_document_id = citation.get(
                "document_id"
            )
            actual_chunk_id = citation.get(
                "chunk_id"
            )

            if (
                actual_document_id
                != expected_document_id
                or actual_chunk_id
                != expected_chunk_id
            ):
                citation_source_mapping_errors.append(
                    {
                        "citation_id": citation_id,
                        "expected_document_id": (
                            expected_document_id
                        ),
                        "actual_document_id": (
                            actual_document_id
                        ),
                        "expected_chunk_id": (
                            expected_chunk_id
                        ),
                        "actual_chunk_id": (
                            actual_chunk_id
                        ),
                    }
                )

        total_raw_citation_count += len(
            raw_citation_ids
        )

        total_valid_citation_count += len(
            valid_citation_ids
        )

        total_invalid_citation_count += len(
            invalid_citation_ids
        )

        total_citation_format_violation_count += len(
            citation_format_violations
        )

        citation_source_mapping_error_count += len(
            citation_source_mapping_errors
        )

        if invalid_citation_ids:
            invalid_citation_case_ids.append(
                case_id
            )

        if citation_format_violations:
            citation_format_violation_case_ids.append(
                case_id
            )

        if citation_source_mapping_errors:
            citation_source_mapping_error_case_ids.append(
                case_id
            )

        per_case[case_id] = {
            "raw_citation_ids": raw_citation_ids,
            "valid_citation_ids": valid_citation_ids,
            "invalid_citation_ids": (
                invalid_citation_ids
            ),
            "citation_format_violations": (
                citation_format_violations
            ),
            "citation_source_mapping_errors": (
                citation_source_mapping_errors
            ),
            "duplicate_source_citation_ids": (
                duplicate_source_citation_ids
            ),
        }

    missing_evidence_case_ids = sorted(
        case_id
        for case_id in answer_with_evidence_case_ids
        if case_id in per_case
        and not per_case[case_id][
            "valid_citation_ids"
        ]
    )

    return {
        "case_integrity": {
            "expected_case_count": len(
                expected_case_ids
            ),
            "result_record_count": len(
                results
            ),
            "unique_case_count": len(
                result_case_id_set
            ),
            "missing_case_ids": (
                missing_case_ids
            ),
            "duplicate_case_ids": (
                duplicate_case_ids
            ),
            "unknown_case_ids": (
                unknown_case_ids
            ),
        },
        "execution": {
            "generation_failure_count": len(
                generation_failure_case_ids
            ),
            "generation_failure_case_ids": (
                generation_failure_case_ids
            ),
            "empty_answer_count": len(
                empty_answer_case_ids
            ),
            "empty_answer_case_ids": (
                empty_answer_case_ids
            ),
        },
        "citations": {
            "total_raw_citation_count": (
                total_raw_citation_count
            ),
            "total_valid_citation_count": (
                total_valid_citation_count
            ),
            "total_invalid_citation_count": (
                total_invalid_citation_count
            ),
            "invalid_citation_case_ids": sorted(
                invalid_citation_case_ids
            ),
            "total_citation_format_violation_count": (
                total_citation_format_violation_count
            ),
            "citation_format_violation_case_ids": sorted(
                citation_format_violation_case_ids
            ),
        },
        "evidence": {
            "answer_with_evidence_case_count": len(
                answer_with_evidence_case_ids
            ),
            "missing_evidence_case_count": len(
                missing_evidence_case_ids
            ),
            "missing_evidence_case_ids": (
                missing_evidence_case_ids
            ),
        },
        "result_integrity": {
            "citation_source_mapping_error_count": (
                citation_source_mapping_error_count
            ),
            "citation_source_mapping_error_case_ids": sorted(
                citation_source_mapping_error_case_ids
            ),
            "duplicate_source_citation_id_count": (
                duplicate_source_citation_id_count
            ),
            "duplicate_source_citation_id_case_ids": sorted(
                duplicate_source_citation_id_case_ids
            ),
        },
        "per_case": per_case,
    }