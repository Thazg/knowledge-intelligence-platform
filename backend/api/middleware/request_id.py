from __future__ import annotations

import logging
import time
import uuid

from starlette.middleware.base import BaseHTTPMiddleware
from starlette.requests import Request
from starlette.responses import Response

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

            latency_ms = (
                time.perf_counter() - start_time
            ) * 1000

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

            response.headers[REQUEST_ID_HEADER] = request_id

            return response

        except Exception:
            latency_ms = (
                time.perf_counter() - start_time
            ) * 1000

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