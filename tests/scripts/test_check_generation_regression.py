from __future__ import annotations

import json

import scripts.check_generation_regression as cli


def test_main_returns_zero_when_generation_regression_passes(
    tmp_path,
    capsys,
) -> None:
    cases_path = tmp_path / "cases.jsonl"
    results_path = tmp_path / "results.jsonl"
    manifest_path = tmp_path / "manifest.json"

    cases_path.write_text(
        json.dumps(
            {
                "case_id": "gen-001",
                "expected_behavior": "answer_with_evidence",
            }
        )
        + "\n",
        encoding="utf-8",
    )

    results_path.write_text(
        json.dumps(
            {
                "case_id": "gen-001",
                "answer": "Supported answer [1].",
                "sources": [
                    {
                        "citation_id": "1",
                        "document_id": "doc-1",
                        "chunk_id": "chunk-1",
                    }
                ],
                "citations": [
                    {
                        "citation_id": "1",
                        "document_id": "doc-1",
                        "chunk_id": "chunk-1",
                    }
                ],
            }
        )
        + "\n",
        encoding="utf-8",
    )

    manifest_path.write_text(
        json.dumps(
            {
                "regression": {
                    "hard_gates": {
                        "case_integrity": {
                            "expected_case_count": 1,
                            "result_record_count": 1,
                            "missing_case_ids": [],
                            "duplicate_case_ids": [],
                            "unknown_case_ids": [],
                        },
                        "execution": {
                            "generation_failure_count": 0,
                            "empty_answer_count": 0,
                        },
                        "citations": {
                            "total_invalid_citation_count": 0,
                        },
                        "evidence": {
                            "missing_evidence_case_count": 0,
                        },
                        "result_integrity": {
                            "citation_source_mapping_error_count": 0,
                            "duplicate_source_citation_id_count": 0,
                        },
                    },
                    "tolerance_gates": {
                        "citation_format_violations": {
                            "maximum_count": 0,
                            "allowed_case_ids": [],
                        }
                    },
                }
            }
        ),
        encoding="utf-8",
    )

    exit_code = cli.main(
        cases_path=cases_path,
        results_path=results_path,
        manifest_path=manifest_path,
    )

    output = json.loads(
        capsys.readouterr().out
    )

    assert exit_code == 0
    assert output["regression"] == {
        "passed": True,
        "failures": [],
    }
    
def test_main_returns_one_when_generation_regression_fails(
    tmp_path,
    capsys,
) -> None:
    cases_path = tmp_path / "cases.jsonl"
    results_path = tmp_path / "results.jsonl"
    manifest_path = tmp_path / "manifest.json"

    cases_path.write_text(
        json.dumps(
            {
                "case_id": "gen-001",
                "expected_behavior": "answer_with_evidence",
            }
        )
        + "\n",
        encoding="utf-8",
    )

    results_path.write_text(
        json.dumps(
            {
                "case_id": "gen-001",
                "answer": "Unsupported citation [99].",
                "sources": [
                    {
                        "citation_id": "1",
                        "document_id": "doc-1",
                        "chunk_id": "chunk-1",
                    }
                ],
                "citations": [],
            }
        )
        + "\n",
        encoding="utf-8",
    )

    manifest_path.write_text(
        json.dumps(
            {
                "regression": {
                    "hard_gates": {
                        "case_integrity": {
                            "expected_case_count": 1,
                            "result_record_count": 1,
                            "missing_case_ids": [],
                            "duplicate_case_ids": [],
                            "unknown_case_ids": [],
                        },
                        "execution": {
                            "generation_failure_count": 0,
                            "empty_answer_count": 0,
                        },
                        "citations": {
                            "total_invalid_citation_count": 0,
                        },
                        "evidence": {
                            "missing_evidence_case_count": 0,
                        },
                        "result_integrity": {
                            "citation_source_mapping_error_count": 0,
                            "duplicate_source_citation_id_count": 0,
                        },
                    },
                    "tolerance_gates": {
                        "citation_format_violations": {
                            "maximum_count": 0,
                            "allowed_case_ids": [],
                        }
                    },
                }
            }
        ),
        encoding="utf-8",
    )

    exit_code = cli.main(
        cases_path=cases_path,
        results_path=results_path,
        manifest_path=manifest_path,
    )

    output = json.loads(
        capsys.readouterr().out
    )

    assert exit_code == 1
    assert output["regression"]["passed"] is False

    assert {
        "type": "hard_gate",
        "section": "citations",
        "metric": "total_invalid_citation_count",
        "expected": 0,
        "actual": 1,
    } in output["regression"]["failures"]