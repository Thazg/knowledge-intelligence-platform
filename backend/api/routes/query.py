from __future__ import annotations

from typing import Annotated

from fastapi import APIRouter, Body, Depends, HTTPException

from backend.api.dependencies import get_rag_service
from backend.api.query_mapper import to_query_response
from backend.api.schemas.query import QueryRequest, QueryResponse
from backend.core.errors import (
    DependencyBusyError,
    DependencyResponseError,
    DependencyTimeoutError,
    DependencyUnavailableError,
)
from backend.services.rag_service import RAGService


QUERY_OPENAPI_EXAMPLES = {
    "docker_buildkit": {
        "summary": "Docker BuildKit",
        "description": (
            "Example query about Docker image builds."
        ),
        "value": {
            "query": (
                "What is Docker BuildKit and how is it "
                "used during image builds?"
            )
        },
    },
    "kubernetes_kubectl": {
        "summary": "Kubernetes kubectl",
        "description": (
            "Example query about declarative Kubernetes "
            "resource management."
        ),
        "value": {
            "query": "What does kubectl apply do?"
        },
    },
    "kubernetes_kms": {
        "summary": "Kubernetes KMS migration",
        "description": (
            "Example version-specific query from the "
            "indexed Kubernetes documentation."
        ),
        "value": {
            "query": (
                "What should Kubernetes users consider "
                "when moving from KMS v1 to KMS v2?"
            )
        },
    },
}


router = APIRouter(
    prefix="/v1",
    tags=["rag"],
)


@router.post(
    "/query",
    response_model=QueryResponse,
)
def query_rag(
    request: Annotated[
        QueryRequest,
        Body(
            openapi_examples=QUERY_OPENAPI_EXAMPLES,
        ),
    ],
    service: RAGService = Depends(get_rag_service),
) -> QueryResponse:
    try:
        result = service.query(request.query)
        return to_query_response(result)

    except DependencyUnavailableError as exc:
        detail = (
            "Vector database is unavailable."
            if exc.dependency == "qdrant"
            else "A required backend service is unavailable."
        )

        raise HTTPException(
            status_code=503,
            detail=detail,
        ) from exc

    except DependencyBusyError as exc:
        raise HTTPException(
            status_code=503,
            detail="A required backend service is busy.",
        ) from exc

    except DependencyTimeoutError as exc:
        raise HTTPException(
            status_code=503,
            detail="A required backend service timed out.",
        ) from exc

    except DependencyResponseError as exc:
        raise HTTPException(
            status_code=503,
            detail="A required backend service returned an error.",
        ) from exc