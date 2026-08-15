from __future__ import annotations

from fastapi import APIRouter, Depends, HTTPException

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


router = APIRouter(
    prefix="/v1",
    tags=["rag"],
)


@router.post(
    "/query",
    response_model=QueryResponse,
)
def query_rag(
    request: QueryRequest,
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