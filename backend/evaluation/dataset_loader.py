from __future__ import annotations

import json
from pathlib import Path

from backend.evaluation.retrieval_evaluator import (
    EvaluationCase,
    RelevantDocument,
)


def load_evaluation_cases(
    path: Path,
    active_only: bool = True,
) -> list[EvaluationCase]:
    cases: list[EvaluationCase] = []

    with path.open(
        "r",
        encoding="utf-8",
    ) as file:
        for line_number, line in enumerate(
            file,
            start=1,
        ):
            line = line.strip()

            if not line:
                continue

            try:
                record = json.loads(line)
            except json.JSONDecodeError as exc:
                raise ValueError(
                    f"Invalid JSON at line {line_number}"
                ) from exc

            if (
                active_only
                and record.get("status") != "active"
            ):
                continue

            case_id = record.get("case_id") or record.get("id")

            if not case_id:
                raise ValueError(
                    "Evaluation case must contain 'case_id' or legacy 'id'"
                )
            query = record["query"]
            category = record.get("category")

            # New schema
            if "relevant_documents" in record:
                relevant_documents = [
                    RelevantDocument(
                        source=document["source"],
                        path=document["path"],
                        relevance=document.get(
                            "relevance",
                            1,
                        ),
                    )
                    for document
                    in record["relevant_documents"]
                ]

                cases.append(
                    EvaluationCase(
                        case_id=case_id,
                        query=query,
                        category=category,
                        relevant_documents=(
                            relevant_documents
                        ),
                    )
                )

                continue

            # Legacy schema
            if (
                "expected_source" in record
                and "expected_path" in record
            ):
                cases.append(
                    EvaluationCase(
                        case_id=case_id,
                        query=query,
                        category=category,
                        expected_source=record[
                            "expected_source"
                        ],
                        expected_path=record[
                            "expected_path"
                        ],
                    )
                )

                continue

            raise ValueError(
                "Evaluation case must contain either "
                "'relevant_documents' or "
                "'expected_source'/'expected_path'. "
                f"Case: {case_id}"
            )

    return cases