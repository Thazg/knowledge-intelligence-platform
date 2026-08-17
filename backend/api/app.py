from __future__ import annotations

import httpx
from fastapi import FastAPI, Response
from fastapi.responses import JSONResponse
from prometheus_client import (
    CONTENT_TYPE_LATEST,
    generate_latest,
)

from backend.api.dependencies import get_rag_service
from backend.api.middleware.request_id import (
    RequestIDMiddleware,
)
from backend.api.routes.query import router as query_router
from backend.api.schemas.health import (
    DependencyStatus,
    ReadinessResponse,
)
from backend.core.config import Settings, get_settings
from backend.core.logging import configure_logging


GROQ_MODELS_URL = (
    "https://api.groq.com/openai/v1/models"
)

configure_logging()


app = FastAPI(
    title=(
        "Enterprise AI Engineering "
        "Knowledge Platform"
    ),
    version="1.0.0",
)

app.add_middleware(
    RequestIDMiddleware
)


@app.get(
    "/health",
    tags=["health"],
)
def health() -> dict[str, str]:
    return {
        "status": "ok",
    }


@app.get(
    "/metrics",
    tags=["metrics"],
)
def metrics() -> Response:
    return Response(
        content=generate_latest(),
        media_type=CONTENT_TYPE_LATEST,
    )


def _check_qdrant(
    settings: Settings,
) -> str:
    try:
        if settings.rag_profile == "cloud":
            if settings.qdrant_api_key is None:
                return "unavailable"

            url = (
                f"{settings.qdrant_url.rstrip('/')}"
                "/collections/"
                f"{settings.qdrant_collection}"
            )

            response = httpx.get(
                url,
                headers={
                    "api-key": (
                        settings.qdrant_api_key
                        .get_secret_value()
                    ),
                },
                timeout=2.0,
            )
        else:
            response = httpx.get(
                settings.qdrant_url,
                timeout=2.0,
            )

        response.raise_for_status()

    except Exception:
        return "unavailable"

    return "ready"


def _check_ollama(
    settings: Settings,
) -> str:
    try:
        response = httpx.get(
            f"{settings.ollama_url}/api/tags",
            timeout=2.0,
        )
        response.raise_for_status()

        payload = response.json()
        models = payload.get(
            "models",
            [],
        )

        available_models = {
            model.get("name")
            for model in models
            if isinstance(
                model,
                dict,
            )
        }

        if (
            settings.generation_model
            not in available_models
        ):
            return "unavailable"

    except Exception:
        return "unavailable"

    return "ready"


def _check_groq(
    settings: Settings,
) -> str:
    if settings.groq_api_key is None:
        return "unavailable"

    try:
        response = httpx.get(
            GROQ_MODELS_URL,
            headers={
                "Authorization": (
                    "Bearer "
                    f"{settings.groq_api_key.get_secret_value()}"
                ),
                "Content-Type": "application/json",
            },
            timeout=2.0,
        )
        response.raise_for_status()

        payload = response.json()
        models = payload.get(
            "data",
            [],
        )

        available_models = {
            model.get("id")
            for model in models
            if isinstance(
                model,
                dict,
            )
        }

        if (
            settings.generation_model
            not in available_models
        ):
            return "unavailable"

    except Exception:
        return "unavailable"

    return "ready"


@app.get(
    "/ready",
    response_model=ReadinessResponse,
    response_model_exclude_none=True,
    tags=["health"],
)
def readiness():
    settings = get_settings()

    rag_status = "ready"

    try:
        get_rag_service()
    except Exception:
        rag_status = "unavailable"

    qdrant_status = _check_qdrant(
        settings
    )

    if settings.rag_profile == "cloud":
        groq_status = _check_groq(
            settings
        )

        dependencies = DependencyStatus(
            rag_service=rag_status,
            qdrant=qdrant_status,
            groq=groq_status,
        )

        all_ready = (
            rag_status == "ready"
            and qdrant_status == "ready"
            and groq_status == "ready"
        )
    else:
        ollama_status = _check_ollama(
            settings
        )

        dependencies = DependencyStatus(
            rag_service=rag_status,
            qdrant=qdrant_status,
            ollama=ollama_status,
        )

        all_ready = (
            rag_status == "ready"
            and qdrant_status == "ready"
            and ollama_status == "ready"
        )

    payload = ReadinessResponse(
        status=(
            "ready"
            if all_ready
            else "not_ready"
        ),
        dependencies=dependencies,
    )

    if not all_ready:
        return JSONResponse(
            status_code=503,
            content=payload.model_dump(
                exclude_none=True,
            ),
        )

    return payload


app.include_router(
    query_router
)