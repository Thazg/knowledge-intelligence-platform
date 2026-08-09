from __future__ import annotations

from prometheus_client import Counter, Histogram


# ---------------------------------------------------------------------------
# HTTP metrics
# ---------------------------------------------------------------------------

HTTP_REQUESTS_TOTAL = Counter(
    "rag_http_requests_total",
    "Total number of HTTP requests.",
    labelnames=("method", "path", "status_code"),
)

HTTP_REQUEST_DURATION_SECONDS = Histogram(
    "rag_http_request_duration_seconds",
    "HTTP request duration in seconds.",
    labelnames=("method", "path"),
    buckets=(
        0.005,
        0.01,
        0.025,
        0.05,
        0.1,
        0.25,
        0.5,
        1.0,
        2.5,
        5.0,
        10.0,
        30.0,
        60.0,
    ),
)


# ---------------------------------------------------------------------------
# RAG metrics
# ---------------------------------------------------------------------------

RAG_QUERIES_TOTAL = Counter(
    "rag_queries_total",
    "Total number of RAG queries.",
    labelnames=("status",),
)

RAG_QUERY_ERRORS_TOTAL = Counter(
    "rag_query_errors_total",
    "Total number of failed RAG queries.",
    labelnames=("error_type",),
)

RAG_RETRIEVAL_DURATION_SECONDS = Histogram(
    "rag_retrieval_duration_seconds",
    "Retrieval stage duration in seconds.",
    buckets=(
        0.01,
        0.025,
        0.05,
        0.1,
        0.25,
        0.5,
        1.0,
        2.5,
        5.0,
    ),
)

RAG_GENERATION_DURATION_SECONDS = Histogram(
    "rag_generation_duration_seconds",
    "Generation stage duration in seconds.",
    buckets=(
        0.5,
        1.0,
        2.5,
        5.0,
        10.0,
        20.0,
        30.0,
        60.0,
    ),
)

RAG_END_TO_END_DURATION_SECONDS = Histogram(
    "rag_end_to_end_duration_seconds",
    "End-to-end RAG pipeline duration in seconds.",
    buckets=(
        0.5,
        1.0,
        2.5,
        5.0,
        10.0,
        20.0,
        30.0,
        60.0,
    ),
)