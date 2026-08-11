from backend.evaluation.generation_evaluator import evaluate_generation_records


def test_evaluate_generation_records_tracks_case_integrity() -> None:
    cases = [
        {
            "case_id": "gen-001",
            "expected_behavior": "answer_with_evidence",
        },
        {
            "case_id": "gen-002",
            "expected_behavior": "answer_with_evidence",
        },
        {
            "case_id": "gen-003",
            "expected_behavior": "qualified_answer",
        },
    ]

    results = [
        {
            "case_id": "gen-001",
            "answer": "Answer [1].",
            "sources": [],
            "citations": [],
        },
        {
            "case_id": "gen-001",
            "answer": "Duplicate result.",
            "sources": [],
            "citations": [],
        },
        {
            "case_id": "gen-999",
            "answer": "Unknown case.",
            "sources": [],
            "citations": [],
        },
    ]

    evaluation = evaluate_generation_records(
        cases=cases,
        results=results,
    )

    case_integrity = evaluation["case_integrity"]

    assert case_integrity["expected_case_count"] == 3
    assert case_integrity["result_record_count"] == 3
    assert case_integrity["unique_case_count"] == 2

    assert case_integrity["missing_case_ids"] == [
        "gen-002",
        "gen-003",
    ]
    assert case_integrity["duplicate_case_ids"] == [
        "gen-001",
    ]
    assert case_integrity["unknown_case_ids"] == [
        "gen-999",
    ]
    
def test_evaluate_generation_records_tracks_execution_failures_and_empty_answers() -> None:
    cases = [
        {
            "case_id": "gen-001",
            "expected_behavior": "answer_with_evidence",
        },
        {
            "case_id": "gen-002",
            "expected_behavior": "answer_with_evidence",
        },
        {
            "case_id": "gen-003",
            "expected_behavior": "qualified_answer",
        },
    ]

    results = [
        {
            "case_id": "gen-001",
            "answer": "Valid answer [1].",
            "sources": [],
            "citations": [],
        },
        {
            "case_id": "gen-002",
            "error": "ReadTimeout",
            "message": "Ollama request timed out.",
        },
        {
            "case_id": "gen-003",
            "answer": "   ",
            "sources": [],
            "citations": [],
        },
    ]

    evaluation = evaluate_generation_records(
        cases=cases,
        results=results,
    )

    execution = evaluation["execution"]

    assert execution["generation_failure_count"] == 1
    assert execution["generation_failure_case_ids"] == [
        "gen-002",
    ]

    assert execution["empty_answer_count"] == 1
    assert execution["empty_answer_case_ids"] == [
        "gen-003",
    ]
    
def test_evaluate_generation_records_detects_invalid_raw_citation_ids() -> None:
    cases = [
        {
            "case_id": "gen-001",
            "expected_behavior": "answer_with_evidence",
        }
    ]

    results = [
        {
            "case_id": "gen-001",
            "answer": "Supported claim [1]. Unsupported claim [99].",
            "sources": [
                {
                    "citation_id": "1",
                    "document_id": "doc-1",
                    "chunk_id": "chunk-1",
                },
                {
                    "citation_id": "2",
                    "document_id": "doc-2",
                    "chunk_id": "chunk-2",
                },
            ],
            "citations": [
                {
                    "citation_id": "1",
                    "document_id": "doc-1",
                    "chunk_id": "chunk-1",
                }
            ],
        }
    ]

    evaluation = evaluate_generation_records(
        cases=cases,
        results=results,
    )

    citations = evaluation["citations"]

    assert citations["total_raw_citation_count"] == 2
    assert citations["total_valid_citation_count"] == 1
    assert citations["total_invalid_citation_count"] == 1

    assert citations["invalid_citation_case_ids"] == [
        "gen-001",
    ]

    case_evaluation = evaluation["per_case"]["gen-001"]

    assert case_evaluation["raw_citation_ids"] == [
        "1",
        "99",
    ]
    assert case_evaluation["valid_citation_ids"] == [
        "1",
    ]
    assert case_evaluation["invalid_citation_ids"] == [
        "99",
    ]
    
def test_evaluate_generation_records_detects_source_style_citation_format_violations() -> None:
    cases = [
        {
            "case_id": "gen-009",
            "expected_behavior": "answer_with_evidence",
        }
    ]

    results = [
        {
            "case_id": "gen-009",
            "answer": (
                "Docker provides deployment guidance [SOURCE 3]. "
                "Kubernetes Deployments are described in [SOURCE 6]. "
                "FastAPI guidance is also available [1]."
            ),
            "sources": [
                {
                    "citation_id": "1",
                    "document_id": "doc-1",
                    "chunk_id": "chunk-1",
                },
                {
                    "citation_id": "3",
                    "document_id": "doc-3",
                    "chunk_id": "chunk-3",
                },
                {
                    "citation_id": "6",
                    "document_id": "doc-6",
                    "chunk_id": "chunk-6",
                },
            ],
            "citations": [
                {
                    "citation_id": "3",
                    "document_id": "doc-3",
                    "chunk_id": "chunk-3",
                },
                {
                    "citation_id": "6",
                    "document_id": "doc-6",
                    "chunk_id": "chunk-6",
                },
                {
                    "citation_id": "1",
                    "document_id": "doc-1",
                    "chunk_id": "chunk-1",
                },
            ],
        }
    ]

    evaluation = evaluate_generation_records(
        cases=cases,
        results=results,
    )

    citations = evaluation["citations"]

    assert citations["total_citation_format_violation_count"] == 2
    assert citations["citation_format_violation_case_ids"] == [
        "gen-009",
    ]

    case_evaluation = evaluation["per_case"]["gen-009"]

    assert case_evaluation["citation_format_violations"] == [
        "[SOURCE 3]",
        "[SOURCE 6]",
    ]
    
def test_evaluate_generation_records_detects_missing_required_evidence() -> None:
    cases = [
        {
            "case_id": "gen-001",
            "expected_behavior": "answer_with_evidence",
        },
        {
            "case_id": "gen-002",
            "expected_behavior": "qualified_answer",
        },
    ]

    results = [
        {
            "case_id": "gen-001",
            "answer": "This answer provides no citation.",
            "sources": [
                {
                    "citation_id": "1",
                    "document_id": "doc-1",
                    "chunk_id": "chunk-1",
                }
            ],
            "citations": [],
        },
        {
            "case_id": "gen-002",
            "answer": "This is a qualified answer without a citation.",
            "sources": [],
            "citations": [],
        },
    ]

    evaluation = evaluate_generation_records(
        cases=cases,
        results=results,
    )

    evidence = evaluation["evidence"]

    assert evidence["answer_with_evidence_case_count"] == 1
    assert evidence["missing_evidence_case_count"] == 1
    assert evidence["missing_evidence_case_ids"] == [
        "gen-001",
    ]
    
def test_evaluate_generation_records_detects_citation_source_mapping_errors() -> None:
    cases = [
        {
            "case_id": "gen-001",
            "expected_behavior": "answer_with_evidence",
        }
    ]

    results = [
        {
            "case_id": "gen-001",
            "answer": "Supported claim [1][2].",
            "sources": [
                {
                    "citation_id": "1",
                    "document_id": "doc-1",
                    "chunk_id": "chunk-1",
                },
                {
                    "citation_id": "2",
                    "document_id": "doc-2",
                    "chunk_id": "chunk-2",
                },
            ],
            "citations": [
                {
                    "citation_id": "1",
                    "document_id": "doc-1",
                    "chunk_id": "chunk-1",
                },
                {
                    "citation_id": "2",
                    "document_id": "wrong-doc",
                    "chunk_id": "wrong-chunk",
                },
            ],
        }
    ]

    evaluation = evaluate_generation_records(
        cases=cases,
        results=results,
    )

    integrity = evaluation["result_integrity"]

    assert integrity["citation_source_mapping_error_count"] == 1
    assert integrity["citation_source_mapping_error_case_ids"] == [
        "gen-001",
    ]

    case_evaluation = evaluation["per_case"]["gen-001"]

    assert case_evaluation["citation_source_mapping_errors"] == [
        {
            "citation_id": "2",
            "expected_document_id": "doc-2",
            "actual_document_id": "wrong-doc",
            "expected_chunk_id": "chunk-2",
            "actual_chunk_id": "wrong-chunk",
        }
    ]
    
def test_evaluate_generation_records_detects_duplicate_source_citation_ids() -> None:
    cases = [
        {
            "case_id": "gen-001",
            "expected_behavior": "answer_with_evidence",
        }
    ]

    results = [
        {
            "case_id": "gen-001",
            "answer": "Supported claim [1].",
            "sources": [
                {
                    "citation_id": "1",
                    "document_id": "doc-1",
                    "chunk_id": "chunk-1",
                },
                {
                    "citation_id": "1",
                    "document_id": "doc-2",
                    "chunk_id": "chunk-2",
                },
            ],
            "citations": [
                {
                    "citation_id": "1",
                    "document_id": "doc-1",
                    "chunk_id": "chunk-1",
                }
            ],
        }
    ]

    evaluation = evaluate_generation_records(
        cases=cases,
        results=results,
    )

    integrity = evaluation["result_integrity"]

    assert integrity["duplicate_source_citation_id_count"] == 1
    assert integrity["duplicate_source_citation_id_case_ids"] == [
        "gen-001",
    ]

    case_evaluation = evaluation["per_case"]["gen-001"]

    assert case_evaluation["duplicate_source_citation_ids"] == [
        "1",
    ]