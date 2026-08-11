from __future__ import annotations

from backend.evaluation.generation_regression import (
    check_generation_regression,
)


def test_generation_regression_passes_approved_evaluation() -> None:
    evaluation = {
        "case_integrity": {
            "expected_case_count": 12,
            "result_record_count": 12,
            "unique_case_count": 12,
            "missing_case_ids": [],
            "duplicate_case_ids": [],
            "unknown_case_ids": [],
        },
        "execution": {
            "generation_failure_count": 0,
            "generation_failure_case_ids": [],
            "empty_answer_count": 0,
            "empty_answer_case_ids": [],
        },
        "citations": {
            "total_raw_citation_count": 82,
            "total_valid_citation_count": 82,
            "total_invalid_citation_count": 0,
            "invalid_citation_case_ids": [],
            "total_citation_format_violation_count": 2,
            "citation_format_violation_case_ids": [
                "gen-009",
            ],
        },
        "evidence": {
            "answer_with_evidence_case_count": 8,
            "missing_evidence_case_count": 0,
            "missing_evidence_case_ids": [],
        },
        "result_integrity": {
            "citation_source_mapping_error_count": 0,
            "citation_source_mapping_error_case_ids": [],
            "duplicate_source_citation_id_count": 0,
            "duplicate_source_citation_id_case_ids": [],
        },
        "per_case": {},
    }

    manifest = {
        "regression": {
            "hard_gates": {
                "case_integrity": {
                    "expected_case_count": 12,
                    "result_record_count": 12,
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
                    "maximum_count": 2,
                    "allowed_case_ids": [
                        "gen-009",
                    ],
                }
            },
        }
    }

    regression = check_generation_regression(
        evaluation=evaluation,
        manifest=manifest,
    )

    assert regression["passed"] is True
    assert regression["failures"] == []
    
def test_generation_regression_fails_when_case_is_missing() -> None:
    evaluation = {
        "case_integrity": {
            "expected_case_count": 12,
            "result_record_count": 11,
            "unique_case_count": 11,
            "missing_case_ids": ["gen-012"],
            "duplicate_case_ids": [],
            "unknown_case_ids": [],
        },
        "execution": {
            "generation_failure_count": 0,
            "generation_failure_case_ids": [],
            "empty_answer_count": 0,
            "empty_answer_case_ids": [],
        },
        "citations": {
            "total_raw_citation_count": 70,
            "total_valid_citation_count": 70,
            "total_invalid_citation_count": 0,
            "invalid_citation_case_ids": [],
            "total_citation_format_violation_count": 0,
            "citation_format_violation_case_ids": [],
        },
        "evidence": {
            "answer_with_evidence_case_count": 8,
            "missing_evidence_case_count": 0,
            "missing_evidence_case_ids": [],
        },
        "result_integrity": {
            "citation_source_mapping_error_count": 0,
            "citation_source_mapping_error_case_ids": [],
            "duplicate_source_citation_id_count": 0,
            "duplicate_source_citation_id_case_ids": [],
        },
        "per_case": {},
    }

    manifest = {
        "regression": {
            "hard_gates": {
                "case_integrity": {
                    "expected_case_count": 12,
                    "result_record_count": 12,
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
                    "maximum_count": 2,
                    "allowed_case_ids": ["gen-009"],
                }
            },
        }
    }

    regression = check_generation_regression(
        evaluation=evaluation,
        manifest=manifest,
    )

    assert regression["passed"] is False

    assert {
        "type": "hard_gate",
        "section": "case_integrity",
        "metric": "result_record_count",
        "expected": 12,
        "actual": 11,
    } in regression["failures"]

    assert {
        "type": "hard_gate",
        "section": "case_integrity",
        "metric": "missing_case_ids",
        "expected": [],
        "actual": ["gen-012"],
    } in regression["failures"]
    
def test_generation_regression_fails_on_execution_errors() -> None:
    evaluation = {
        "case_integrity": {
            "expected_case_count": 12,
            "result_record_count": 12,
            "unique_case_count": 12,
            "missing_case_ids": [],
            "duplicate_case_ids": [],
            "unknown_case_ids": [],
        },
        "execution": {
            "generation_failure_count": 1,
            "generation_failure_case_ids": ["gen-005"],
            "empty_answer_count": 1,
            "empty_answer_case_ids": ["gen-006"],
        },
        "citations": {
            "total_raw_citation_count": 70,
            "total_valid_citation_count": 70,
            "total_invalid_citation_count": 0,
            "invalid_citation_case_ids": [],
            "total_citation_format_violation_count": 0,
            "citation_format_violation_case_ids": [],
        },
        "evidence": {
            "answer_with_evidence_case_count": 8,
            "missing_evidence_case_count": 0,
            "missing_evidence_case_ids": [],
        },
        "result_integrity": {
            "citation_source_mapping_error_count": 0,
            "citation_source_mapping_error_case_ids": [],
            "duplicate_source_citation_id_count": 0,
            "duplicate_source_citation_id_case_ids": [],
        },
        "per_case": {},
    }

    manifest = {
        "regression": {
            "hard_gates": {
                "case_integrity": {
                    "expected_case_count": 12,
                    "result_record_count": 12,
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
                    "maximum_count": 2,
                    "allowed_case_ids": ["gen-009"],
                }
            },
        }
    }

    regression = check_generation_regression(
        evaluation=evaluation,
        manifest=manifest,
    )

    assert regression["passed"] is False

    assert {
        "type": "hard_gate",
        "section": "execution",
        "metric": "generation_failure_count",
        "expected": 0,
        "actual": 1,
    } in regression["failures"]

    assert {
        "type": "hard_gate",
        "section": "execution",
        "metric": "empty_answer_count",
        "expected": 0,
        "actual": 1,
    } in regression["failures"]
    
def test_generation_regression_fails_on_quality_structure_errors() -> None:
    evaluation = {
        "case_integrity": {
            "expected_case_count": 12,
            "result_record_count": 12,
            "unique_case_count": 12,
            "missing_case_ids": [],
            "duplicate_case_ids": [],
            "unknown_case_ids": [],
        },
        "execution": {
            "generation_failure_count": 0,
            "generation_failure_case_ids": [],
            "empty_answer_count": 0,
            "empty_answer_case_ids": [],
        },
        "citations": {
            "total_raw_citation_count": 80,
            "total_valid_citation_count": 79,
            "total_invalid_citation_count": 1,
            "invalid_citation_case_ids": [
                "gen-003",
            ],
            "total_citation_format_violation_count": 0,
            "citation_format_violation_case_ids": [],
        },
        "evidence": {
            "answer_with_evidence_case_count": 8,
            "missing_evidence_case_count": 1,
            "missing_evidence_case_ids": [
                "gen-007",
            ],
        },
        "result_integrity": {
            "citation_source_mapping_error_count": 1,
            "citation_source_mapping_error_case_ids": [
                "gen-010",
            ],
            "duplicate_source_citation_id_count": 0,
            "duplicate_source_citation_id_case_ids": [],
        },
        "per_case": {},
    }

    manifest = {
        "regression": {
            "hard_gates": {
                "case_integrity": {
                    "expected_case_count": 12,
                    "result_record_count": 12,
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
                    "maximum_count": 2,
                    "allowed_case_ids": [
                        "gen-009",
                    ],
                }
            },
        }
    }

    regression = check_generation_regression(
        evaluation=evaluation,
        manifest=manifest,
    )

    assert regression["passed"] is False

    assert {
        "type": "hard_gate",
        "section": "citations",
        "metric": "total_invalid_citation_count",
        "expected": 0,
        "actual": 1,
    } in regression["failures"]

    assert {
        "type": "hard_gate",
        "section": "evidence",
        "metric": "missing_evidence_case_count",
        "expected": 0,
        "actual": 1,
    } in regression["failures"]

    assert {
        "type": "hard_gate",
        "section": "result_integrity",
        "metric": "citation_source_mapping_error_count",
        "expected": 0,
        "actual": 1,
    } in regression["failures"]
    
def test_generation_regression_fails_on_duplicate_source_citation_ids() -> None:
    evaluation = {
        "case_integrity": {
            "expected_case_count": 12,
            "result_record_count": 12,
            "unique_case_count": 12,
            "missing_case_ids": [],
            "duplicate_case_ids": [],
            "unknown_case_ids": [],
        },
        "execution": {
            "generation_failure_count": 0,
            "generation_failure_case_ids": [],
            "empty_answer_count": 0,
            "empty_answer_case_ids": [],
        },
        "citations": {
            "total_raw_citation_count": 82,
            "total_valid_citation_count": 82,
            "total_invalid_citation_count": 0,
            "invalid_citation_case_ids": [],
            "total_citation_format_violation_count": 0,
            "citation_format_violation_case_ids": [],
        },
        "evidence": {
            "answer_with_evidence_case_count": 8,
            "missing_evidence_case_count": 0,
            "missing_evidence_case_ids": [],
        },
        "result_integrity": {
            "citation_source_mapping_error_count": 0,
            "citation_source_mapping_error_case_ids": [],
            "duplicate_source_citation_id_count": 1,
            "duplicate_source_citation_id_case_ids": [
                "gen-001",
            ],
        },
        "per_case": {},
    }

    manifest = {
        "regression": {
            "hard_gates": {
                "case_integrity": {
                    "expected_case_count": 12,
                    "result_record_count": 12,
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
                    "maximum_count": 2,
                    "allowed_case_ids": [
                        "gen-009",
                    ],
                }
            },
        }
    }

    regression = check_generation_regression(
        evaluation=evaluation,
        manifest=manifest,
    )

    assert regression["passed"] is False

    assert {
        "type": "hard_gate",
        "section": "result_integrity",
        "metric": "duplicate_source_citation_id_count",
        "expected": 0,
        "actual": 1,
    } in regression["failures"]
    
def test_generation_regression_allows_fewer_format_violations() -> None:
    evaluation = {
        "case_integrity": {
            "expected_case_count": 12,
            "result_record_count": 12,
            "unique_case_count": 12,
            "missing_case_ids": [],
            "duplicate_case_ids": [],
            "unknown_case_ids": [],
        },
        "execution": {
            "generation_failure_count": 0,
            "generation_failure_case_ids": [],
            "empty_answer_count": 0,
            "empty_answer_case_ids": [],
        },
        "citations": {
            "total_raw_citation_count": 75,
            "total_valid_citation_count": 75,
            "total_invalid_citation_count": 0,
            "invalid_citation_case_ids": [],
            "total_citation_format_violation_count": 0,
            "citation_format_violation_case_ids": [],
        },
        "evidence": {
            "answer_with_evidence_case_count": 8,
            "missing_evidence_case_count": 0,
            "missing_evidence_case_ids": [],
        },
        "result_integrity": {
            "citation_source_mapping_error_count": 0,
            "citation_source_mapping_error_case_ids": [],
            "duplicate_source_citation_id_count": 0,
            "duplicate_source_citation_id_case_ids": [],
        },
        "per_case": {},
    }

    manifest = {
        "regression": {
            "hard_gates": {
                "case_integrity": {
                    "expected_case_count": 12,
                    "result_record_count": 12,
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
                    "maximum_count": 2,
                    "allowed_case_ids": [
                        "gen-009",
                    ],
                }
            },
        }
    }

    regression = check_generation_regression(
        evaluation=evaluation,
        manifest=manifest,
    )

    assert regression["passed"] is True
    assert regression["failures"] == []
    
def test_generation_regression_fails_when_format_violation_count_exceeds_maximum() -> None:
    evaluation = {
        "case_integrity": {
            "expected_case_count": 12,
            "result_record_count": 12,
            "unique_case_count": 12,
            "missing_case_ids": [],
            "duplicate_case_ids": [],
            "unknown_case_ids": [],
        },
        "execution": {
            "generation_failure_count": 0,
            "generation_failure_case_ids": [],
            "empty_answer_count": 0,
            "empty_answer_case_ids": [],
        },
        "citations": {
            "total_raw_citation_count": 82,
            "total_valid_citation_count": 82,
            "total_invalid_citation_count": 0,
            "invalid_citation_case_ids": [],
            "total_citation_format_violation_count": 3,
            "citation_format_violation_case_ids": [
                "gen-009",
            ],
        },
        "evidence": {
            "answer_with_evidence_case_count": 8,
            "missing_evidence_case_count": 0,
            "missing_evidence_case_ids": [],
        },
        "result_integrity": {
            "citation_source_mapping_error_count": 0,
            "citation_source_mapping_error_case_ids": [],
            "duplicate_source_citation_id_count": 0,
            "duplicate_source_citation_id_case_ids": [],
        },
        "per_case": {},
    }

    manifest = {
        "regression": {
            "hard_gates": {
                "case_integrity": {
                    "expected_case_count": 12,
                    "result_record_count": 12,
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
                    "maximum_count": 2,
                    "allowed_case_ids": [
                        "gen-009",
                    ],
                }
            },
        }
    }

    regression = check_generation_regression(
        evaluation=evaluation,
        manifest=manifest,
    )

    assert regression["passed"] is False

    assert {
        "type": "tolerance_gate",
        "metric": "citation_format_violation_count",
        "maximum": 2,
        "actual": 3,
    } in regression["failures"]
    
def test_generation_regression_fails_when_format_violation_moves_to_unapproved_case() -> None:
    evaluation = {
        "case_integrity": {
            "expected_case_count": 12,
            "result_record_count": 12,
            "unique_case_count": 12,
            "missing_case_ids": [],
            "duplicate_case_ids": [],
            "unknown_case_ids": [],
        },
        "execution": {
            "generation_failure_count": 0,
            "generation_failure_case_ids": [],
            "empty_answer_count": 0,
            "empty_answer_case_ids": [],
        },
        "citations": {
            "total_raw_citation_count": 82,
            "total_valid_citation_count": 82,
            "total_invalid_citation_count": 0,
            "invalid_citation_case_ids": [],
            "total_citation_format_violation_count": 1,
            "citation_format_violation_case_ids": [
                "gen-003",
            ],
        },
        "evidence": {
            "answer_with_evidence_case_count": 8,
            "missing_evidence_case_count": 0,
            "missing_evidence_case_ids": [],
        },
        "result_integrity": {
            "citation_source_mapping_error_count": 0,
            "citation_source_mapping_error_case_ids": [],
            "duplicate_source_citation_id_count": 0,
            "duplicate_source_citation_id_case_ids": [],
        },
        "per_case": {},
    }

    manifest = {
        "regression": {
            "hard_gates": {
                "case_integrity": {
                    "expected_case_count": 12,
                    "result_record_count": 12,
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
                    "maximum_count": 2,
                    "allowed_case_ids": [
                        "gen-009",
                    ],
                }
            },
        }
    }

    regression = check_generation_regression(
        evaluation=evaluation,
        manifest=manifest,
    )

    assert regression["passed"] is False

    assert {
        "type": "tolerance_gate",
        "metric": "citation_format_violation_case_ids",
        "allowed": ["gen-009"],
        "unexpected": ["gen-003"],
    } in regression["failures"]