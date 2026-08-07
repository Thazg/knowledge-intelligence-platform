from __future__ import annotations

from dataclasses import dataclass
from typing import Protocol

from backend.retrieval.models import RetrievalResult


class RetrieverProtocol(Protocol):
    def retrieve(
        self,
        query: str,
        top_k: int = 5,
        max_chunks_per_document: int | None = None,
        candidate_multiplier: int = 5,
    ) -> list[RetrievalResult]:
        ...


@dataclass(frozen=True)
class RelevantDocument:
    source: str
    path: str
    relevance: int = 1

    def __post_init__(self) -> None:
        if self.relevance < 1:
            raise ValueError(
                "relevance must be >= 1"
            )


@dataclass
class EvaluationCase:
    case_id: str
    query: str

    relevant_documents: list[
        RelevantDocument
    ] | None = None

    category: str | None = None

    # Legacy fields
    expected_source: str | None = None
    expected_path: str | None = None

    def __post_init__(self) -> None:
        if not self.query.strip():
            raise ValueError(
                "query must not be empty"
            )

        if self.relevant_documents:
            return

        if (
            self.expected_source is not None
            and self.expected_path is not None
        ):
            self.relevant_documents = [
                RelevantDocument(
                    source=self.expected_source,
                    path=self.expected_path,
                    relevance=3,
                )
            ]

            return

        raise ValueError(
            "EvaluationCase requires either "
            "relevant_documents or legacy "
            "expected_source/expected_path."
        )


@dataclass
class RetrievedDocument:
    source: str
    path: str
    rank: int
    relevance: int


@dataclass
class EvaluationResult:
    case_id: str
    query: str
    category: str | None

    relevant_documents: list[
        RelevantDocument
    ]

    retrieved_paths: list[str]

    first_relevant_rank: int | None

    retrieved_relevant_documents: list[
        RetrievedDocument
    ]

    @property
    def reciprocal_rank(self) -> float:
        if self.first_relevant_rank is None:
            return 0.0

        return (
            1.0
            / self.first_relevant_rank
        )

    def hit_at_k(
        self,
        k: int,
    ) -> bool:
        if k < 1:
            raise ValueError(
                "k must be >= 1"
            )

        return (
            self.first_relevant_rank
            is not None
            and self.first_relevant_rank <= k
        )

    def recall_at_k(
        self,
        k: int,
    ) -> float:
        if k < 1:
            raise ValueError(
                "k must be >= 1"
            )

        if not self.relevant_documents:
            return 0.0

        relevant_keys = {
            (
                document.source.lower(),
                _normalize_path(
                    document.path
                ),
            )
            for document
            in self.relevant_documents
        }

        retrieved_keys = {
            (
                document.source.lower(),
                _normalize_path(
                    document.path
                ),
            )
            for document
            in self.retrieved_relevant_documents
            if document.rank <= k
        }

        matched = (
            relevant_keys
            & retrieved_keys
        )

        return (
            len(matched)
            / len(relevant_keys)
        )


class RetrievalEvaluator:

    def __init__(
        self,
        retriever: RetrieverProtocol,
    ) -> None:
        self.retriever = retriever

    def evaluate_case(
        self,
        case: EvaluationCase,
        top_k: int = 10,
    ) -> EvaluationResult:

        if top_k < 1:
            raise ValueError(
                "top_k must be >= 1"
            )

        retrieved = (
            self.retriever.retrieve(
                query=case.query,
                top_k=top_k,
                max_chunks_per_document=1,
                candidate_multiplier=5,
            )
        )

        relevant_documents = (
            case.relevant_documents
            or []
        )

        relevance_lookup = {
            (
                document.source.lower(),
                _normalize_path(
                    document.path
                ),
            ): document.relevance
            for document
            in relevant_documents
        }

        retrieved_paths: list[str] = []

        retrieved_relevant_documents: list[
            RetrievedDocument
        ] = []

        first_relevant_rank: (
            int | None
        ) = None

        for position, result in enumerate(
            retrieved,
            start=1,
        ):
            result_source = (
                result.source.lower()
            )

            result_path = (
                _normalize_path(
                    result.relative_path
                )
            )

            retrieved_paths.append(
                result.relative_path
            )

            relevance = (
                relevance_lookup.get(
                    (
                        result_source,
                        result_path,
                    ),
                    0,
                )
            )

            if relevance <= 0:
                continue

            rank = (
                result.rank
                if result.rank is not None
                else position
            )

            retrieved_relevant_documents.append(
                RetrievedDocument(
                    source=result.source,
                    path=result.relative_path,
                    rank=rank,
                    relevance=relevance,
                )
            )

            if first_relevant_rank is None:
                first_relevant_rank = rank

        return EvaluationResult(
            case_id=case.case_id,
            query=case.query,
            category=case.category,
            relevant_documents=(
                relevant_documents
            ),
            retrieved_paths=retrieved_paths,
            first_relevant_rank=(
                first_relevant_rank
            ),
            retrieved_relevant_documents=(
                retrieved_relevant_documents
            ),
        )

    def evaluate(
        self,
        cases: list[EvaluationCase],
        top_k: int = 10,
    ) -> list[EvaluationResult]:

        return [
            self.evaluate_case(
                case=case,
                top_k=top_k,
            )
            for case in cases
        ]


def _normalize_path(
    path: str,
) -> str:
    return (
        path
        .replace("\\", "/")
        .lower()
    )