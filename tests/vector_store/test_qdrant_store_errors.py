from __future__ import annotations

import httpx
import numpy as np
import pytest

from qdrant_client.http.exceptions import ResponseHandlingException

from backend.core.errors import DependencyUnavailableError
from backend.vector_store.qdrant_store import QdrantVectorStore


def test_search_translates_transport_failure_to_dependency_unavailable(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    store = QdrantVectorStore(
        collection_name="test_collection",
        vector_size=3,
        url="http://qdrant:6333",
    )

    def fail_query_points(
        **_kwargs: object,
    ) -> None:
        raise ResponseHandlingException(
            httpx.ConnectError(
                "Qdrant unavailable",
            )
        )

    monkeypatch.setattr(
        store.client,
        "query_points",
        fail_query_points,
    )

    query_embedding = np.array(
        [0.1, 0.2, 0.3],
        dtype=np.float32,
    )

    with pytest.raises(
        DependencyUnavailableError,
    ) as exc_info:
        store.search(
            query_embedding=query_embedding,
            limit=5,
        )

    assert exc_info.value.dependency == "qdrant"
    assert isinstance(
        exc_info.value.__cause__,
        ResponseHandlingException,
    )