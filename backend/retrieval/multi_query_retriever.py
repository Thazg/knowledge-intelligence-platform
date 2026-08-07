from __future__ import annotations

from collections import defaultdict
from typing import Protocol

from backend.retrieval.models import RetrievalResult


class QueryRewriterProtocol(Protocol):
    def rewrite(
        self,
        query: str,
    ) -> list[str]:
        ...


class MultiQueryRetriever:
    def __init__(
        self,
        base_retriever,
        query_rewriter: QueryRewriterProtocol,
        rrf_k: int = 60,
        candidate_multiplier: int = 5,
        query_weights: list[float] | None = None,
    ) -> None:
        if rrf_k <= 0:
            raise ValueError(
                "rrf_k must be > 0"
            )

        if candidate_multiplier < 1:
            raise ValueError(
                "candidate_multiplier must be >= 1"
            )

        if query_weights is not None:
            if not query_weights:
                raise ValueError(
                    "query_weights must not be empty"
                )

            if any(
                weight < 0
                for weight in query_weights
            ):
                raise ValueError(
                    "query_weights must be >= 0"
                )

            if all(
                weight == 0
                for weight in query_weights
            ):
                raise ValueError(
                    "At least one query weight must be > 0"
                )

        self.base_retriever = base_retriever
        self.query_rewriter = query_rewriter
        self.rrf_k = rrf_k
        self.candidate_multiplier = (
            candidate_multiplier
        )
        self.query_weights = query_weights

    def retrieve(
        self,
        query: str,
        top_k: int = 5,
        max_chunks_per_document: int | None = 1,
        candidate_multiplier: int | None = None,
    ) -> list[RetrievalResult]:
        query = query.strip()

        if not query:
            raise ValueError(
                "query must not be empty"
            )

        if top_k < 1:
            raise ValueError(
                "top_k must be >= 1"
            )

        if (
            max_chunks_per_document is not None
            and max_chunks_per_document < 1
        ):
            raise ValueError(
                "max_chunks_per_document must be >= 1 "
                "or None"
            )

        queries = self.query_rewriter.rewrite(
            query
        )

        if not queries:
            raise ValueError(
                "query_rewriter returned no queries"
            )

        query_weights = self._resolve_query_weights(
            number_of_queries=len(queries)
        )

        effective_candidate_multiplier = (
            candidate_multiplier
            if candidate_multiplier is not None
            else self.candidate_multiplier
        )

        if effective_candidate_multiplier < 1:
            raise ValueError(
                "candidate_multiplier must be >= 1"
            )

        candidate_k = (
            top_k
            * effective_candidate_multiplier
        )

        fused_scores: dict[str, float] = (
            defaultdict(float)
        )

        result_by_chunk_id: dict[
            str,
            RetrievalResult,
        ] = {}

        for rewritten_query, query_weight in zip(
            queries,
            query_weights,
        ):
            results = (
                self.base_retriever.retrieve(
                    query=rewritten_query,
                    top_k=candidate_k,
                    max_chunks_per_document=None,
                    candidate_multiplier=5,
                )
            )

            for rank, result in enumerate(
                results,
                start=1,
            ):
                fused_scores[
                    result.chunk_id
                ] += (
                    query_weight
                    / (self.rrf_k + rank)
                )

                result_by_chunk_id[
                    result.chunk_id
                ] = result

        ranked_chunk_ids = sorted(
            fused_scores,
            key=fused_scores.get,
            reverse=True,
        )

        final_results: list[
            RetrievalResult
        ] = []

        document_counts: dict[
            str,
            int,
        ] = defaultdict(int)

        for chunk_id in ranked_chunk_ids:
            result = result_by_chunk_id[
                chunk_id
            ]

            if (
                max_chunks_per_document
                is not None
            ):
                if (
                    document_counts[
                        result.document_id
                    ]
                    >= max_chunks_per_document
                ):
                    continue

                document_counts[
                    result.document_id
                ] += 1

            result.score = fused_scores[
                chunk_id
            ]

            result.rank = (
                len(final_results) + 1
            )

            final_results.append(
                result
            )

            if len(final_results) >= top_k:
                break

        return final_results

    def _resolve_query_weights(
        self,
        number_of_queries: int,
    ) -> list[float]:
        if self.query_weights is None:
            return [
                1.0
                for _ in range(
                    number_of_queries
                )
            ]

        if (
            len(self.query_weights)
            != number_of_queries
        ):
            raise ValueError(
                "query_weights length must match "
                "the number of generated queries. "
                f"Expected {number_of_queries}, "
                f"received "
                f"{len(self.query_weights)}."
            )

        return self.query_weights