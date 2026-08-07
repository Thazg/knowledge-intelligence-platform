from sentence_transformers import CrossEncoder

from backend.retrieval.models import RetrievalResult


class CrossEncoderReranker:
    def __init__(
        self,
        model_name: str = (
            "cross-encoder/ms-marco-MiniLM-L6-v2"
        ),
        batch_size: int = 16,
    ) -> None:
        if batch_size <= 0:
            raise ValueError(
                "batch_size must be greater than 0."
            )

        self.model_name = model_name
        self.batch_size = batch_size

        self.model = CrossEncoder(
            model_name_or_path=model_name,
        )

    def rerank(
        self,
        query: str,
        candidates: list[RetrievalResult],
        top_k: int | None = None,
    ) -> list[RetrievalResult]:
        if not query.strip():
            raise ValueError(
                "query must not be empty."
            )

        if not candidates:
            return []

        if top_k is not None and top_k <= 0:
            raise ValueError(
                "top_k must be greater than 0."
            )

        pairs = [
            (
                query,
                self._build_passage(candidate),
            )
            for candidate in candidates
        ]

        scores = self.model.predict(
            inputs=pairs,
            batch_size=self.batch_size,
            show_progress_bar=False,
        )

        scored_candidates = sorted(
            zip(candidates, scores, strict=True),
            key=lambda item: float(item[1]),
            reverse=True,
        )

        limit = (
            len(scored_candidates)
            if top_k is None
            else min(top_k, len(scored_candidates))
        )

        reranked_results: list[RetrievalResult] = []

        for rank, (candidate, score) in enumerate(
            scored_candidates[:limit],
            start=1,
        ):
            reranked_results.append(
                RetrievalResult(
                    chunk_id=candidate.chunk_id,
                    document_id=candidate.document_id,
                    content=candidate.content,
                    score=float(score),
                    rank=rank,
                    source=candidate.source,
                    filename=candidate.filename,
                    relative_path=candidate.relative_path,
                    chunk_index=candidate.chunk_index,
                    token_count=candidate.token_count,
                    title=candidate.title,
                )
            )

        return reranked_results
    
    @staticmethod
    def _build_passage(
        candidate: RetrievalResult,
    ) -> str:
        parts: list[str] = []

        if candidate.title:
            parts.append(
                f"Title: {candidate.title}"
            )

        if candidate.source:
            parts.append(
                f"Source: {candidate.source}"
            )

        if candidate.relative_path:
            parts.append(
                f"Path: {candidate.relative_path}"
            )

        parts.append(
            f"Content: {candidate.content}"
        )

        return "\n".join(parts)