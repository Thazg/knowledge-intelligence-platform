from backend.reranking.cross_encoder_reranker import (
    CrossEncoderReranker,
)
from backend.retrieval.hybrid_retriever import HybridRetriever
from backend.retrieval.models import RetrievalResult


class RerankedRetriever:
    def __init__(
        self,
        base_retriever: HybridRetriever,
        reranker: CrossEncoderReranker,
        candidate_multiplier: int = 2,
    ) -> None:
        if candidate_multiplier <= 0:
            raise ValueError(
                "candidate_multiplier must be greater than 0."
            )

        self.base_retriever = base_retriever
        self.reranker = reranker
        self.candidate_multiplier = candidate_multiplier

    def retrieve(
        self,
        query: str,
        top_k: int = 5,
        max_chunks_per_document: int | None = 1,
        candidate_multiplier: int | None = None,
    ) -> list[RetrievalResult]:
        if not query.strip():
            raise ValueError("query must not be empty.")

        if top_k <= 0:
            raise ValueError(
                "top_k must be greater than 0."
            )

        effective_multiplier = (
            self.candidate_multiplier
            if candidate_multiplier is None
            else candidate_multiplier
        )

        if effective_multiplier <= 0:
            raise ValueError(
                "candidate_multiplier must be greater than 0."
            )

        candidate_k = top_k * effective_multiplier

        candidates = self.base_retriever.retrieve(
            query=query,
            top_k=candidate_k,
            max_chunks_per_document=max_chunks_per_document,
            candidate_multiplier=5,
        )

        return self.reranker.rerank(
            query=query,
            candidates=candidates,
            top_k=top_k,
        )