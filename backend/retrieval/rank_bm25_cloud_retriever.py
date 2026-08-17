from __future__ import annotations

from typing import Any, Protocol

from backend.retrieval.models import RetrievalResult


class SparseQueryEncoder(Protocol):
    def encode(
        self,
        query: str,
    ) -> Any | None:
        ...


class QdrantSparseQueryClient(Protocol):
    def query_points(
        self,
        **kwargs: Any,
    ) -> Any:
        ...


class RankBM25CloudRetriever:
    def __init__(
        self,
        encoder: SparseQueryEncoder,
        client: QdrantSparseQueryClient,
        collection_name: str,
        vector_name: str,
    ) -> None:
        if not collection_name.strip():
            raise ValueError(
                "collection_name must not be empty."
            )

        if not vector_name.strip():
            raise ValueError(
                "vector_name must not be empty."
            )

        self.encoder = encoder
        self.client = client
        self.collection_name = collection_name
        self.vector_name = vector_name

    def retrieve(
        self,
        query: str,
        top_k: int = 5,
        max_chunks_per_document: int | None = None,
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
                "max_chunks_per_document "
                "must be greater than 0."
            )

        if candidate_multiplier <= 0:
            raise ValueError(
                "candidate_multiplier "
                "must be greater than 0."
            )

        query_vector = self.encoder.encode(
            query
        )

        if query_vector is None:
            return []

        search_limit = top_k

        if max_chunks_per_document is not None:
            search_limit = (
                top_k * candidate_multiplier
            )

        response = self.client.query_points(
            collection_name=self.collection_name,
            query=query_vector,
            using=self.vector_name,
            limit=search_limit,
            with_payload=True,
        )

        results: list[RetrievalResult] = []
        document_counts: dict[str, int] = {}

        for point in response.points:
            score = float(point.score)

            # Match the existing local BM25
            # retriever behavior.
            if score <= 0:
                continue

            payload = point.payload or {}

            document_id = str(
                payload.get(
                    "document_id",
                    "",
                )
            )

            if max_chunks_per_document is not None:
                current_count = (
                    document_counts.get(
                        document_id,
                        0,
                    )
                )

                if (
                    current_count
                    >= max_chunks_per_document
                ):
                    continue

                document_counts[document_id] = (
                    current_count + 1
                )

            results.append(
                RetrievalResult(
                    chunk_id=str(
                        payload.get(
                            "chunk_id",
                            "",
                        )
                    ),
                    document_id=document_id,
                    content=str(
                        payload.get(
                            "content",
                            "",
                        )
                    ),
                    score=score,
                    rank=len(results) + 1,
                    source=str(
                        payload.get(
                            "source",
                            "",
                        )
                    ),
                    filename=str(
                        payload.get(
                            "filename",
                            "",
                        )
                    ),
                    relative_path=str(
                        payload.get(
                            "relative_path",
                            "",
                        )
                    ),
                    chunk_index=int(
                        payload.get(
                            "chunk_index",
                            0,
                        )
                    ),
                    token_count=int(
                        payload.get(
                            "token_count",
                            0,
                        )
                    ),
                    title=payload.get(
                        "title"
                    ),
                )
            )

            if len(results) >= top_k:
                break

        return results