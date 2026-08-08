from __future__ import annotations

import httpx

from fastapi import FastAPI
from fastapi.responses import JSONResponse

from backend.api.dependencies import get_rag_service
from backend.api.routes.query import router as query_router
from backend.api.schemas.health import (
    DependencyStatus,
    ReadinessResponse,
)


app = FastAPI(
    title="Enterprise AI Engineering Knowledge Platform",
    version="1.0.0",
)


@app.get("/health", tags=["health"])
def health() -> dict[str, str]:
    return {
        "status": "ok",
    }


@app.get(
    "/ready",
    response_model=ReadinessResponse,
    tags=["health"],
)
def readiness():
    rag_status = "ready"
    qdrant_status = "ready"
    ollama_status = "ready"

    try:
        get_rag_service()
    except Exception:
        rag_status = "unavailable"

    try:
        response = httpx.get(
            "http://localhost:6333",
            timeout=2.0,
        )
        response.raise_for_status()
    except Exception:
        qdrant_status = "unavailable"

    try:
        response = httpx.get(
            "http://localhost:11434/api/tags",
            timeout=2.0,
        )
        response.raise_for_status()
    except Exception:
        ollama_status = "unavailable"

    all_ready = (
        rag_status == "ready"
        and qdrant_status == "ready"
        and ollama_status == "ready"
    )

    payload = ReadinessResponse(
        status="ready" if all_ready else "not_ready",
        dependencies=DependencyStatus(
            rag_service=rag_status,
            qdrant=qdrant_status,
            ollama=ollama_status,
        ),
    )

    if not all_ready:
        return JSONResponse(
            status_code=503,
            content=payload.model_dump(),
        )

    return payload


app.include_router(query_router)