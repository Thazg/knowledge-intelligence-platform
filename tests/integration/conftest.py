import uuid

import pytest

from backend.vector_store.qdrant_store import QdrantVectorStore


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