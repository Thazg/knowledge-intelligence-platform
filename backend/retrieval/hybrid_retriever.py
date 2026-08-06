from collections import defaultdict

from backend.retrieval.bm25_retriever import BM25Retriever
from backend.retrieval.dense_retriever import DenseRetriever
from backend.retrieval.models import RetrievalResult


class HybridRetriever:
    def __init__(
        self,
        dense_retriever: DenseRetriever,
        bm25_retriever: BM25Retriever,
        rrf_k: int = 60,
    ) -> None:
        if rrf_k <= 0:
            raise ValueError("rrf_k must be greater than 0.")

        self.dense_retriever = dense_retriever
        self.bm25_retriever = bm25_retriever
        self.rrf_k = rrf_k

    def retrieve(
        self,
        query: str,
        top_k: int = 5,
        candidate_k: int = 30,
        max_chunks_per_document: int | None = 1,
    ) -> list[RetrievalResult]:
        if not query.strip():
            raise ValueError("query must not be empty.")

        if top_k <= 0:
            raise ValueError(
                "top_k must be greater than 0."
            )

        if candidate_k < top_k:
            raise ValueError(
                "candidate_k must be greater than "
                "or equal to top_k."
            )

        dense_results = self.dense_retriever.retrieve(
            query=query,
            top_k=candidate_k,
            max_chunks_per_document=None,
        )

        bm25_results = self.bm25_retriever.retrieve(
            query=query,
            top_k=candidate_k,
            max_chunks_per_document=None,
        )

        fused_scores: dict[str, float] = defaultdict(float)
        result_by_chunk_id: dict[str, RetrievalResult] = {}

        for result in dense_results:
            fused_scores[result.chunk_id] += (
                1.0 / (self.rrf_k + result.rank)
            )
            result_by_chunk_id[result.chunk_id] = result

        for result in bm25_results:
            fused_scores[result.chunk_id] += (
                1.0 / (self.rrf_k + result.rank)
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

        document_counts: dict[str, int] = defaultdict(int)
        results: list[RetrievalResult] = []

        for chunk_id in sorted_chunk_ids:
            original = result_by_chunk_id[chunk_id]

            if max_chunks_per_document is not None:
                if (
                    document_counts[original.document_id]
                    >= max_chunks_per_document
                ):
                    continue

                document_counts[original.document_id] += 1

            results.append(
                RetrievalResult(
                    chunk_id=original.chunk_id,
                    document_id=original.document_id,
                    content=original.content,
                    score=fused_scores[chunk_id],
                    rank=len(results) + 1,
                    source=original.source,
                    filename=original.filename,
                    relative_path=original.relative_path,
                    chunk_index=original.chunk_index,
                    token_count=original.token_count,
                    title=original.title,
                )
            )

            if len(results) >= top_k:
                break

        return results