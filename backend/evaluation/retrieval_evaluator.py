from dataclasses import dataclass
from typing import Protocol
from backend.retrieval.dense_retriever import DenseRetriever
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


@dataclass
class EvaluationCase:
    case_id: str
    query: str
    expected_source: str
    expected_path: str


@dataclass
class EvaluationResult:
    case_id: str
    query: str
    expected_path: str
    retrieved_paths: list[str]
    first_relevant_rank: int | None

    @property
    def reciprocal_rank(self) -> float:
        if self.first_relevant_rank is None:
            return 0.0

        return 1.0 / self.first_relevant_rank

    def hit_at_k(self, k: int) -> bool:
        return (
            self.first_relevant_rank is not None
            and self.first_relevant_rank <= k
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

        retrieved = self.retriever.retrieve(
            query=case.query,
            top_k=top_k,
            max_chunks_per_document=1,
            candidate_multiplier=5,
        )

        expected_source = case.expected_source.lower()
        expected_path = (
            case.expected_path
            .replace("\\", "/")
            .lower()
        )

        retrieved_paths: list[str] = []
        first_relevant_rank: int | None = None

        for result in retrieved:
            result_source = result.source.lower()

            result_path = (
                result.relative_path
                .replace("\\", "/")
                .lower()
            )

            retrieved_paths.append(
                result.relative_path
            )

            is_relevant = (
                result_source == expected_source
                and result_path == expected_path
            )

            if (
                is_relevant
                and first_relevant_rank is None
            ):
                first_relevant_rank = result.rank

        return EvaluationResult(
            case_id=case.case_id,
            query=case.query,
            expected_path=case.expected_path,
            retrieved_paths=retrieved_paths,
            first_relevant_rank=first_relevant_rank,
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