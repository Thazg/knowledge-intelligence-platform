import uuid

import numpy as np
import pytest

from backend.chunking.models import Chunk
from backend.vector_store.qdrant_store import QdrantVectorStore

pytestmark = pytest.mark.integration

@pytest.fixture
def qdrant_store():
    collection_name = (
        f"enterprise_knowledge_integration_test_{uuid.uuid4().hex}"
    )

    store = QdrantVectorStore(
        collection_name=collection_name,
        vector_size=3,
    )

    store.create_collection()

    try:
        yield store
    finally:
        store.client.delete_collection(
            collection_name=collection_name,
        )

def test_qdrant_store_upsert_and_search(qdrant_store):
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

    inserted = qdrant_store.upsert_chunks(
        chunks=chunks,
        embeddings=embeddings,
    )

    assert inserted == 3

    query_embedding = np.array(
        [1.0, 0.0, 0.0],
        dtype=np.float32,
    )

    results = qdrant_store.search(
        query_embedding=query_embedding,
        limit=3,
    )

    assert len(results) == 3

    top_result = results[0]

    assert top_result.payload["chunk_id"] == "chunk-kubernetes"
    assert top_result.payload["document_id"] == "doc-kubernetes"
    assert (
        top_result.payload["content"]
        == "Kubernetes Deployments manage replicated Pods."
    )
    assert top_result.payload["source"] == "kubernetes"