import numpy as np
import pytest

from backend.chunking.models import Chunk
from backend.retrieval.dense_retriever import DenseRetriever

pytestmark = pytest.mark.integration


class FakeEmbedder:
    def embed_query(self, query: str) -> np.ndarray:
        return np.array(
            [1.0, 0.0, 0.0],
            dtype=np.float32,
        )


def test_dense_retriever_returns_expected_qdrant_result(qdrant_store):
    chunks = [
        Chunk(
            chunk_id="chunk-kubernetes",
            document_id="doc-kubernetes",
            content="Kubernetes Deployments manage replicated Pods.",
            chunk_index=0,
            token_count=6,
            source="kubernetes",
            filename="deployments.md",
            relative_path="kubernetes/deployments.md",
            title="Deployments",
        ),
        Chunk(
            chunk_id="chunk-fastapi",
            document_id="doc-fastapi",
            content="FastAPI uses Pydantic models for request validation.",
            chunk_index=0,
            token_count=7,
            source="fastapi",
            filename="validation.md",
            relative_path="fastapi/validation.md",
            title="Request Validation",
        ),
        Chunk(
            chunk_id="chunk-qdrant",
            document_id="doc-qdrant",
            content="Qdrant provides vector similarity search.",
            chunk_index=0,
            token_count=5,
            source="qdrant",
            filename="search.md",
            relative_path="qdrant/search.md",
            title="Vector Search",
        ),
    ]

    embeddings = np.array(
        [
            [1.0, 0.0, 0.0],
            [0.0, 1.0, 0.0],
            [0.0, 0.0, 1.0],
        ],
        dtype=np.float32,
    )

    qdrant_store.upsert_chunks(
        chunks=chunks,
        embeddings=embeddings,
    )

    retriever = DenseRetriever(
        embedder=FakeEmbedder(),
        vector_store=qdrant_store,
    )

    results = retriever.retrieve(
        query="How do Kubernetes Deployments work?",
        top_k=3,
    )

    assert len(results) == 3

    top_result = results[0]

    assert top_result.rank == 1
    assert top_result.chunk_id == "chunk-kubernetes"
    assert top_result.document_id == "doc-kubernetes"
    assert top_result.source == "kubernetes"
    assert top_result.title == "Deployments"