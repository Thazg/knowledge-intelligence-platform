from __future__ import annotations

import json
from collections.abc import Iterator
from typing import Annotated

from fastapi import APIRouter, Body, Depends, HTTPException
from fastapi.responses import StreamingResponse

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
    service: Annotated[RAGService, Depends(get_rag_service)],
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


def _encode_sse(
    event: str,
    data: dict[str, object],
) -> str:
    payload = json.dumps(
        data,
        ensure_ascii=False,
        separators=(",", ":"),
    )
    return f"event: {event}\ndata: {payload}\n\n"


def _stream_error(
    exc: Exception,
) -> dict[str, object]:
    if isinstance(
        exc,
        DependencyBusyError,
    ):
        return {
            "code": "generation_busy",
            "message": (
                "The generator is handling another request. "
                "Please retry shortly."
            ),
            "retryable": True,
        }

    if isinstance(
        exc,
        DependencyTimeoutError,
    ):
        return {
            "code": "generation_timeout",
            "message": (
                "Answer generation timed out. Please retry."
            ),
            "retryable": True,
        }

    if isinstance(
        exc,
        DependencyUnavailableError,
    ):
        return {
            "code": "backend_unavailable",
            "message": (
                "A required backend service is unavailable. "
                "Please retry shortly."
            ),
            "retryable": True,
        }

    if isinstance(
        exc,
        DependencyResponseError,
    ):
        return {
            "code": "backend_response_error",
            "message": (
                "A required backend service returned an error. "
                "Please retry."
            ),
            "retryable": True,
        }

    return {
        "code": "stream_error",
        "message": (
            "The answer stream ended unexpectedly. "
            "Please retry."
        ),
        "retryable": True,
    }


def _query_event_stream(
    *,
    query: str,
    service: RAGService,
) -> Iterator[str]:
    try:
        for event in service.stream(query):
            if event.event == "status":
                yield _encode_sse(
                    "status",
                    {
                        "status": event.status,
                    },
                )
                continue

            if event.event == "answer_delta":
                yield _encode_sse(
                    "answer_delta",
                    {
                        "delta": event.delta or "",
                    },
                )
                continue

            if (
                event.event == "done"
                and event.result is not None
            ):
                response = to_query_response(
                    event.result
                )

                yield _encode_sse(
                    "citations",
                    {
                        "citations": [
                            citation.model_dump()
                            for citation in response.citations
                        ],
                        "sources": [
                            source.model_dump()
                            for source in response.sources
                        ],
                    },
                )
                yield _encode_sse(
                    "done",
                    {
                        "query": response.query,
                        "model": response.model,
                        "metrics": (
                            response.metrics.model_dump()
                        ),
                    },
                )

    except Exception as exc:
        yield _encode_sse(
            "error",
            _stream_error(exc),
        )


@router.post(
    "/query/stream",
    response_class=StreamingResponse,
    responses={
        200: {
            "content": {
                "text/event-stream": {}
            },
            "description": (
                "Grounded answer as Server-Sent Events."
            ),
        }
    },
)
def stream_query_rag(
    request: Annotated[
        QueryRequest,
        Body(
            openapi_examples=(
                QUERY_OPENAPI_EXAMPLES
            ),
        ),
    ],
    service: Annotated[RAGService, Depends(get_rag_service)],
) -> StreamingResponse:
    return StreamingResponse(
        _query_event_stream(
            query=request.query,
            service=service,
        ),
        media_type="text/event-stream",
        headers={
            "Cache-Control": "no-cache, no-transform",
            "X-Accel-Buffering": "no",
        },
    )
