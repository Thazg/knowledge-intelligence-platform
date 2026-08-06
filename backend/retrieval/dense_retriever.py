from backend.embedding.embedder import LocalEmbedder
from backend.retrieval.models import RetrievalResult
from backend.vector_store.qdrant_store import QdrantVectorStore


class DenseRetriever:

    def __init__(
        self,
        embedder: LocalEmbedder,
        vector_store: QdrantVectorStore,
    ) -> None:
        self.embedder = embedder
        self.vector_store = vector_store

    def retrieve(
        self,
        query: str,
        top_k: int = 5,
        score_threshold: float | None = None,
        max_chunks_per_document: int | None = None,
        candidate_multiplier: int = 3,
    ) -> list[RetrievalResult]:

        if not query.strip():
            raise ValueError("query must not be empty.")

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

        query_embedding = self.embedder.embed_query(
            query
        )

        search_limit = top_k

        if max_chunks_per_document is not None:
            search_limit = (
                top_k * candidate_multiplier
            )

        points = self.vector_store.search(
            query_embedding=query_embedding,
            limit=search_limit,
        )

        results: list[RetrievalResult] = []

        document_counts: dict[str, int] = {}

        for point in points:
            if (
                score_threshold is not None
                and point.score < score_threshold
            ):
                continue

            payload = point.payload or {}

            document_id = str(
                payload.get("document_id", "")
            )

            if max_chunks_per_document is not None:
                current_count = document_counts.get(
                    document_id,
                    0,
                )

                if (
                    current_count
                    >= max_chunks_per_document
                ):
                    continue

                document_counts[document_id] = (
                    current_count + 1
                )

            result = RetrievalResult(
                chunk_id=str(
                    payload.get("chunk_id", "")
                ),
                document_id=document_id,
                content=str(
                    payload.get("content", "")
                ),
                score=float(point.score),
                rank=len(results) + 1,
                source=str(
                    payload.get("source", "")
                ),
                filename=str(
                    payload.get("filename", "")
                ),
                relative_path=str(
                    payload.get("relative_path", "")
                ),
                chunk_index=int(
                    payload.get("chunk_index", 0)
                ),
                token_count=int(
                    payload.get("token_count", 0)
                ),
                title=payload.get("title"),
            )

            results.append(result)

            if len(results) >= top_k:
                break

        return results