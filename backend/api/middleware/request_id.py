from __future__ import annotations

import logging
import time
import uuid

from starlette.middleware.base import BaseHTTPMiddleware
from starlette.requests import Request
from starlette.responses import Response

from backend.core.metrics import (
    HTTP_REQUEST_DURATION_SECONDS,
    HTTP_REQUESTS_TOTAL,
)
from backend.core.request_context import request_id_context


REQUEST_ID_HEADER = "X-Request-ID"

logger = logging.getLogger(__name__)


class RequestIDMiddleware(BaseHTTPMiddleware):
    async def dispatch(
        self,
        request: Request,
        call_next,
    ) -> Response:
        request_id = request.headers.get(
            REQUEST_ID_HEADER,
            str(uuid.uuid4()),
        )

        request.state.request_id = request_id

        token = request_id_context.set(request_id)

        start_time = time.perf_counter()

        try:
            logger.info(
                "Request started method=%s path=%s",
                request.method,
                request.url.path,
            )

            response = await call_next(request)

            duration_seconds = (
                time.perf_counter() - start_time
            )

            latency_ms = duration_seconds * 1000

            logger.info(
                (
                    "Request completed method=%s path=%s "
                    "status_code=%d latency_ms=%.2f"
                ),
                request.method,
                request.url.path,
                response.status_code,
                latency_ms,
            )

            HTTP_REQUESTS_TOTAL.labels(
                method=request.method,
                path=request.url.path,
                status_code=str(response.status_code),
            ).inc()

            HTTP_REQUEST_DURATION_SECONDS.labels(
                method=request.method,
                path=request.url.path,
            ).observe(duration_seconds)

            response.headers[
                REQUEST_ID_HEADER
            ] = request_id

            return response

        except Exception:
            duration_seconds = (
                time.perf_counter() - start_time
            )

            latency_ms = duration_seconds * 1000

            HTTP_REQUESTS_TOTAL.labels(
                method=request.method,
                path=request.url.path,
                status_code="500",
            ).inc()

            HTTP_REQUEST_DURATION_SECONDS.labels(
                method=request.method,
                path=request.url.path,
            ).observe(duration_seconds)

            logger.exception(
                (
                    "Request failed method=%s path=%s "
                    "latency_ms=%.2f"
                ),
                request.method,
                request.url.path,
                latency_ms,
            )

            raise

        finally:
            request_id_context.reset(token)