from collections import defaultdict
from typing import Protocol

from backend.retrieval.models import RetrievalResult


class RankedRetriever(Protocol):
    def retrieve(
        self,
        query: str,
        top_k: int = 5,
        max_chunks_per_document: int | None = None,
    ) -> list[RetrievalResult]:
        ...


class HybridRetriever:
    def __init__(
        self,
        dense_retriever: RankedRetriever,
        bm25_retriever: RankedRetriever,
        rrf_k: int = 60,
        dense_weight: float = 0.7,
        bm25_weight: float = 0.3,
    ) -> None:
        if rrf_k <= 0:
            raise ValueError(
                "rrf_k must be greater than 0."
            )

        if dense_weight < 0:
            raise ValueError(
                "dense_weight must be greater than or equal to 0."
            )

        if bm25_weight < 0:
            raise ValueError(
                "bm25_weight must be greater than or equal to 0."
            )

        if dense_weight + bm25_weight <= 0:
            raise ValueError(
                "At least one retrieval weight must be greater than 0."
            )

        self.dense_retriever = dense_retriever
        self.bm25_retriever = bm25_retriever
        self.rrf_k = rrf_k
        self.dense_weight = dense_weight
        self.bm25_weight = bm25_weight

    def retrieve(
        self,
        query: str,
        top_k: int = 5,
        max_chunks_per_document: int | None = 1,
        candidate_multiplier: int = 5,
    ) -> list[RetrievalResult]:
        if not query.strip():
            raise ValueError(
                "query must not be empty."
            )

        if top_k <= 0:
            raise ValueError(
                "top_k must be greater than 0."
            )

        if (
            max_chunks_per_document is not None
            and max_chunks_per_document <= 0
        ):
            raise ValueError(
                "max_chunks_per_document must be greater than 0."
            )

        if candidate_multiplier <= 0:
            raise ValueError(
                "candidate_multiplier must be greater than 0."
            )

        candidate_k = (
            top_k * candidate_multiplier
        )

        dense_results = (
            self.dense_retriever.retrieve(
                query=query,
                top_k=candidate_k,
                max_chunks_per_document=None,
            )
        )

        bm25_results = (
            self.bm25_retriever.retrieve(
                query=query,
                top_k=candidate_k,
                max_chunks_per_document=None,
            )
        )

        fused_scores: dict[str, float] = (
            defaultdict(float)
        )

        result_by_chunk_id: dict[
            str,
            RetrievalResult,
        ] = {}

        for result in dense_results:
            fused_scores[result.chunk_id] += (
                self.dense_weight
                / (
                    self.rrf_k
                    + result.rank
                )
            )

            result_by_chunk_id[
                result.chunk_id
            ] = result

        for result in bm25_results:
            fused_scores[result.chunk_id] += (
                self.bm25_weight
                / (
                    self.rrf_k
                    + result.rank
                )
            )

            result_by_chunk_id.setdefault(
                result.chunk_id,
                result,
            )

        sorted_chunk_ids = sorted(
            fused_scores,
            key=fused_scores.get,
            reverse=True,
        )

        document_counts: dict[
            str,
            int,
        ] = defaultdict(int)

        results: list[RetrievalResult] = []

        for chunk_id in sorted_chunk_ids:
            original = (
                result_by_chunk_id[
                    chunk_id
                ]
            )

            if (
                max_chunks_per_document
                is not None
            ):
                if (
                    document_counts[
                        original.document_id
                    ]
                    >= max_chunks_per_document
                ):
                    continue

                document_counts[
                    original.document_id
                ] += 1

            results.append(
                RetrievalResult(
                    chunk_id=original.chunk_id,
                    document_id=(
                        original.document_id
                    ),
                    content=original.content,
                    score=(
                        fused_scores[
                            chunk_id
                        ]
                    ),
                    rank=len(results) + 1,
                    source=original.source,
                    filename=(
                        original.filename
                    ),
                    relative_path=(
                        original.relative_path
                    ),
                    chunk_index=(
                        original.chunk_index
                    ),
                    token_count=(
                        original.token_count
                    ),
                    title=original.title,
                )
            )

            if len(results) >= top_k:
                break

        return results