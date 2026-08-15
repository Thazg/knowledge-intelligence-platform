from __future__ import annotations

import httpx

from fastapi import APIRouter, Depends, HTTPException
from qdrant_client.http.exceptions import ResponseHandlingException

from backend.api.dependencies import get_rag_service
from backend.api.query_mapper import to_query_response
from backend.api.schemas.query import QueryRequest, QueryResponse
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

    except ResponseHandlingException as exc:
        raise HTTPException(
            status_code=503,
            detail="Vector database is unavailable.",
        ) from exc

    except httpx.ConnectError as exc:
        raise HTTPException(
            status_code=503,
            detail="A required backend service is unavailable.",
        ) from exc

    except httpx.TimeoutException as exc:
        raise HTTPException(
            status_code=503,
            detail="A required backend service timed out.",
        ) from exc
 
    except httpx.HTTPStatusError as exc:
        raise HTTPException(
            status_code=503,
            detail="A required backend service returned an error.",
        ) from exc
