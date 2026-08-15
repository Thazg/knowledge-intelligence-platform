import uuid

import numpy as np
from numpy.typing import NDArray
from qdrant_client import QdrantClient, models
from backend.chunking.models import Chunk
from qdrant_client.http.exceptions import ResponseHandlingException
from backend.core.errors import DependencyUnavailableError

class QdrantVectorStore:

    def __init__(
        self,
        collection_name: str,
        vector_size: int,
        url: str = "http://localhost:6333",
    ) -> None:

        if not collection_name.strip():
            raise ValueError(
                "collection_name must not be empty."
            )

        if vector_size <= 0:
            raise ValueError(
                "vector_size must be greater than 0."
            )

        self.collection_name = collection_name
        self.vector_size = vector_size

        self.client = QdrantClient(url=url)

    def collection_exists(self) -> bool:
        return self.client.collection_exists(
            collection_name=self.collection_name,
        )

    def create_collection(self) -> bool:

        if self.collection_exists():
            return False

        self.client.create_collection(
            collection_name=self.collection_name,
            vectors_config=models.VectorParams(
                size=self.vector_size,
                distance=models.Distance.COSINE,
            ),
        )

        return True

    def upsert_chunks(
        self,
        chunks: list[Chunk],
        embeddings: NDArray[np.float32],
        wait: bool = True,
    ) -> int:

        if len(chunks) != len(embeddings):
            raise ValueError(
                "The number of chunks must match "
                "the number of embeddings."
            )

        if embeddings.ndim != 2:
            raise ValueError(
                "embeddings must be a 2-dimensional array."
            )

        if embeddings.shape[1] != self.vector_size:
            raise ValueError(
                "Embedding dimension does not match "
                f"collection vector size: "
                f"{embeddings.shape[1]} != {self.vector_size}."
            )

        if not chunks:
            return 0

        points: list[models.PointStruct] = []

        for chunk, embedding in zip(
            chunks,
            embeddings,
            strict=True,
        ):
            points.append(
                models.PointStruct(
                    id=self._to_qdrant_id(
                        chunk.chunk_id
                    ),
                    vector=embedding.tolist(),
                    payload={
                        "chunk_id": chunk.chunk_id,
                        "document_id": (
                            chunk.document_id
                        ),
                        "content": chunk.content,
                        "chunk_index": (
                            chunk.chunk_index
                        ),
                        "token_count": (
                            chunk.token_count
                        ),
                        "source": chunk.source,
                        "filename": chunk.filename,
                        "relative_path": (
                            chunk.relative_path
                        ),
                        "title": chunk.title,
                    },
                )
            )

        self.client.upsert(
            collection_name=self.collection_name,
            points=points,
            wait=wait,
        )

        return len(points)

    @staticmethod
    def _to_qdrant_id(
        chunk_id: str,
    ) -> str:

        return str(
            uuid.uuid5(
                uuid.NAMESPACE_URL,
                chunk_id,
            )
        )
        
    def search(
        self,
        query_embedding: NDArray[np.float32],
        limit: int = 5,
    ) -> list[models.ScoredPoint]:

        if limit <= 0:
            raise ValueError(
                "limit must be greater than 0."
            )

        if query_embedding.ndim != 1:
            raise ValueError(
                "query_embedding must be "
                "a 1-dimensional vector."
            )

        if query_embedding.shape[0] != self.vector_size:
            raise ValueError(
                "Query embedding dimension does not match "
                f"collection vector size: "
                f"{query_embedding.shape[0]} "
                f"!= {self.vector_size}."
            )

        try:
            response = self.client.query_points(
                collection_name=self.collection_name,
                query=query_embedding.tolist(),
                limit=limit,
                with_payload=True,
                with_vectors=False,
            )

        except ResponseHandlingException as exc:
            raise DependencyUnavailableError(
                "qdrant"
            ) from exc

        return response.points