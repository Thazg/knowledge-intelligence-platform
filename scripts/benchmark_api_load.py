from __future__ import annotations

import argparse
import asyncio
import json
import random
import statistics
import time
from collections import Counter
from datetime import datetime, timezone
from itertools import count
from pathlib import Path
from typing import Any

import httpx


DEFAULT_QUERY = "What is a Kubernetes Deployment?"
BUSY_DETAIL = "A required backend service is busy."
DEFAULT_SEED = 20260816


def _percentile(
    values: list[float],
    percentile: float,
) -> float:
    if not values:
        raise ValueError("values must not be empty")

    ordered = sorted(values)

    if len(ordered) == 1:
        return ordered[0]

    position = (len(ordered) - 1) * percentile
    lower_index = int(position)
    upper_index = min(
        lower_index + 1,
        len(ordered) - 1,
    )
    fraction = position - lower_index

    return ordered[lower_index] + (
        ordered[upper_index] - ordered[lower_index]
    ) * fraction


def _latency_summary(
    values: list[float],
) -> dict[str, float | int] | None:
    if not values:
        return None

    return {
        "count": len(values),
        "mean": statistics.fmean(values),
        "median": statistics.median(values),
        "p50": _percentile(values, 0.50),
        "p95": _percentile(values, 0.95),
        "p99": _percentile(values, 0.99),
        "min": min(values),
        "max": max(values),
    }


def _json_body(
    response: httpx.Response,
) -> dict[str, Any] | None:
    try:
        payload = response.json()
    except ValueError:
        return None

    if isinstance(payload, dict):
        return payload

    return None


def _classify_response(
    status_code: int,
    body: dict[str, Any] | None,
) -> str:
    if status_code == 200:
        return "success"

    detail = body.get("detail") if body is not None else None

    if status_code == 503 and detail == BUSY_DETAIL:
        return "busy"

    if status_code == 503:
        return "dependency_503"

    if status_code == 422:
        return "validation_error"

    if status_code >= 500:
        return "server_error"

    return "http_error"


async def _send_request(
    client: httpx.AsyncClient,
    *,
    base_url: str,
    query: str,
    request_id: str,
    request_number: int,
    run_start: float | None = None,
    scheduled_offset_ms: float | None = None,
) -> dict[str, Any]:
    start = time.perf_counter()

    launch_offset_ms = None
    launch_lag_ms = None

    if run_start is not None:
        launch_offset_ms = (start - run_start) * 1000

        if scheduled_offset_ms is not None:
            launch_lag_ms = (
                launch_offset_ms - scheduled_offset_ms
            )

    try:
        response = await client.post(
            f"{base_url}/v1/query",
            json={"query": query},
            headers={"X-Request-ID": request_id},
        )
    except httpx.TimeoutException as exc:
        end = time.perf_counter()
        latency_ms = (end - start) * 1000

        return {
            "request_number": request_number,
            "request_id_sent": request_id,
            "request_id_received": None,
            "status_code": None,
            "classification": "client_timeout",
            "latency_ms": latency_ms,
            "detail": str(exc),
            "metrics": None,
            "scheduled_offset_ms": scheduled_offset_ms,
            "launch_offset_ms": launch_offset_ms,
            "launch_lag_ms": launch_lag_ms,
            "completion_offset_ms": (
                (end - run_start) * 1000
                if run_start is not None
                else None
            ),
        }
    except httpx.RequestError as exc:
        end = time.perf_counter()
        latency_ms = (end - start) * 1000

        return {
            "request_number": request_number,
            "request_id_sent": request_id,
            "request_id_received": None,
            "status_code": None,
            "classification": "client_error",
            "latency_ms": latency_ms,
            "detail": str(exc),
            "metrics": None,
            "scheduled_offset_ms": scheduled_offset_ms,
            "launch_offset_ms": launch_offset_ms,
            "launch_lag_ms": launch_lag_ms,
            "completion_offset_ms": (
                (end - run_start) * 1000
                if run_start is not None
                else None
            ),
        }

    end = time.perf_counter()
    latency_ms = (end - start) * 1000
    body = _json_body(response)
    classification = _classify_response(
        response.status_code,
        body,
    )

    detail: Any = None
    metrics: dict[str, Any] | None = None

    if body is not None:
        detail = body.get("detail")

        raw_metrics = body.get("metrics")

        if isinstance(raw_metrics, dict):
            metrics = raw_metrics

    return {
        "request_number": request_number,
        "request_id_sent": request_id,
        "request_id_received": response.headers.get(
            "X-Request-ID"
        ),
        "status_code": response.status_code,
        "classification": classification,
        "latency_ms": latency_ms,
        "detail": detail,
        "metrics": metrics,
        "scheduled_offset_ms": scheduled_offset_ms,
        "launch_offset_ms": launch_offset_ms,
        "launch_lag_ms": launch_lag_ms,
        "completion_offset_ms": (
            (end - run_start) * 1000
            if run_start is not None
            else None
        ),
    }


async def _run_warmup(
    client: httpx.AsyncClient,
    *,
    base_url: str,
    query: str,
    run_id: str,
    warmup_requests: int,
) -> None:
    for index in range(1, warmup_requests + 1):
        print(
            f"Warm-up request "
            f"{index}/{warmup_requests}..."
        )

        result = await _send_request(
            client,
            base_url=base_url,
            query=query,
            request_id=(
                f"lt-{run_id}-warmup-{index:03d}"
            ),
            request_number=index,
        )

        if result["classification"] != "success":
            raise RuntimeError(
                "Warm-up request failed: "
                f"classification="
                f"{result['classification']} "
                f"status="
                f"{result['status_code']} "
                f"detail="
                f"{result['detail']}"
            )

        print(
            "Warm-up completed "
            f"latency_ms="
            f"{result['latency_ms']:.2f}"
        )


async def _run_measured_requests(
    client: httpx.AsyncClient,
    *,
    base_url: str,
    query: str,
    run_id: str,
    request_count: int,
    concurrency: int,
) -> tuple[list[dict[str, Any]], float]:
    semaphore = asyncio.Semaphore(concurrency)
    start_gate = asyncio.Event()
    run_start = 0.0

    async def run_one(
        request_number: int,
    ) -> dict[str, Any]:
        await start_gate.wait()

        async with semaphore:
            return await _send_request(
                client,
                base_url=base_url,
                query=query,
                request_id=(
                    f"lt-{run_id}-"
                    f"{request_number:04d}"
                ),
                request_number=request_number,
                run_start=run_start,
            )

    tasks = [
        asyncio.create_task(
            run_one(request_number)
        )
        for request_number in range(
            1,
            request_count + 1,
        )
    ]

    run_start = time.perf_counter()
    start_gate.set()

    results = await asyncio.gather(*tasks)

    wall_time_ms = (
        time.perf_counter() - run_start
    ) * 1000

    return results, wall_time_ms


async def _run_sustained_requests(
    client: httpx.AsyncClient,
    *,
    base_url: str,
    query: str,
    run_id: str,
    duration_seconds: float,
    concurrency: int,
) -> tuple[list[dict[str, Any]], float]:
    start_gate = asyncio.Event()
    request_numbers = count(1)
    run_start = 0.0
    deadline = 0.0

    async def run_worker() -> list[dict[str, Any]]:
        worker_results: list[dict[str, Any]] = []

        await start_gate.wait()

        while time.perf_counter() < deadline:
            request_number = next(request_numbers)

            result = await _send_request(
                client,
                base_url=base_url,
                query=query,
                request_id=(
                    f"lt-{run_id}-"
                    f"sustained-{request_number:05d}"
                ),
                request_number=request_number,
                run_start=run_start,
            )

            worker_results.append(result)

        return worker_results

    tasks = [
        asyncio.create_task(run_worker())
        for _ in range(concurrency)
    ]

    run_start = time.perf_counter()
    deadline = run_start + duration_seconds
    start_gate.set()

    worker_results = await asyncio.gather(*tasks)

    wall_time_ms = (
        time.perf_counter() - run_start
    ) * 1000

    results = [
        result
        for worker_result in worker_results
        for result in worker_result
    ]

    results.sort(
        key=lambda result: result["request_number"]
    )

    return results, wall_time_ms


def _fixed_arrival_offsets(
    *,
    duration_seconds: float,
    rate_rps: float,
) -> list[float]:
    interval_seconds = 1.0 / rate_rps
    offsets: list[float] = []
    offset = 0.0

    while offset < duration_seconds:
        offsets.append(offset)
        offset += interval_seconds

    return offsets


def _poisson_arrival_offsets(
    *,
    duration_seconds: float,
    rate_rps: float,
    seed: int,
) -> list[float]:
    rng = random.Random(seed)
    offsets: list[float] = []
    offset = 0.0

    while True:
        offset += rng.expovariate(rate_rps)

        if offset >= duration_seconds:
            break

        offsets.append(offset)

    return offsets


async def _run_fixed_rate_requests(
    client: httpx.AsyncClient,
    *,
    base_url: str,
    query: str,
    run_id: str,
    duration_seconds: float,
    rate_rps: float,
    arrival_model: str,
    seed: int,
) -> tuple[
    list[dict[str, Any]],
    float,
    list[float],
]:
    if arrival_model == "fixed":
        arrival_offsets = _fixed_arrival_offsets(
            duration_seconds=duration_seconds,
            rate_rps=rate_rps,
        )
    else:
        arrival_offsets = _poisson_arrival_offsets(
            duration_seconds=duration_seconds,
            rate_rps=rate_rps,
            seed=seed,
        )

    if not arrival_offsets:
        raise RuntimeError(
            "Arrival schedule produced no requests. "
            "Increase duration or rate."
        )

    tasks: list[
        asyncio.Task[dict[str, Any]]
    ] = []

    run_start = time.perf_counter()

    for request_number, offset_seconds in enumerate(
        arrival_offsets,
        start=1,
    ):
        target_time = run_start + offset_seconds
        sleep_seconds = (
            target_time - time.perf_counter()
        )

        if sleep_seconds > 0:
            await asyncio.sleep(sleep_seconds)

        tasks.append(
            asyncio.create_task(
                _send_request(
                    client,
                    base_url=base_url,
                    query=query,
                    request_id=(
                        f"lt-{run_id}-"
                        f"rate-{request_number:05d}"
                    ),
                    request_number=request_number,
                    run_start=run_start,
                    scheduled_offset_ms=(
                        offset_seconds * 1000
                    ),
                )
            )
        )

    results = await asyncio.gather(*tasks)

    wall_time_ms = (
        time.perf_counter() - run_start
    ) * 1000

    results.sort(
        key=lambda result: result[
            "request_number"
        ]
    )

    return (
        results,
        wall_time_ms,
        arrival_offsets,
    )


def _numeric_metric_values(
    results: list[dict[str, Any]],
    metric_name: str,
) -> list[float]:
    values: list[float] = []

    for result in results:
        if result["classification"] != "success":
            continue

        metrics = result.get("metrics")

        if not isinstance(metrics, dict):
            continue

        value = metrics.get(metric_name)

        if (
            isinstance(value, (int, float))
            and not isinstance(value, bool)
        ):
            values.append(float(value))

    return values


def _numeric_result_values(
    results: list[dict[str, Any]],
    field_name: str,
) -> list[float]:
    values: list[float] = []

    for result in results:
        value = result.get(field_name)

        if (
            isinstance(value, (int, float))
            and not isinstance(value, bool)
        ):
            values.append(float(value))

    return values


def _error_details(
    results: list[dict[str, Any]],
) -> list[dict[str, Any]]:
    return [
        {
            "request_number": result["request_number"],
            "status_code": result["status_code"],
            "classification": result["classification"],
            "detail": result["detail"],
            "latency_ms": result["latency_ms"],
        }
        for result in results
        if result["classification"]
        not in {"success", "busy"}
    ]


def _classification_sequence(
    results: list[dict[str, Any]],
) -> list[str]:
    return [
        str(result["classification"])
        for result in results
    ]


def _build_summary(
    results: list[dict[str, Any]],
    wall_time_ms: float,
) -> dict[str, Any]:
    classifications = Counter(
        str(result["classification"])
        for result in results
    )

    status_codes = Counter(
        (
            str(result["status_code"])
            if result["status_code"] is not None
            else "client_error"
        )
        for result in results
    )

    all_latencies = [
        float(result["latency_ms"])
        for result in results
    ]

    success_latencies = [
        float(result["latency_ms"])
        for result in results
        if result["classification"] == "success"
    ]

    busy_latencies = [
        float(result["latency_ms"])
        for result in results
        if result["classification"] == "busy"
    ]

    successful_requests = classifications.get(
        "success",
        0,
    )
    busy_requests = classifications.get(
        "busy",
        0,
    )
    total_requests = len(results)

    if total_requests < 1:
        raise RuntimeError(
            "Measured workload produced no requests."
        )

    wall_time_seconds = wall_time_ms / 1000

    request_id_mismatches = sum(
        1
        for result in results
        if (
            result["request_id_received"]
            != result["request_id_sent"]
        )
    )

    stage_metric_names = (
        "retrieval_latency_ms",
        "context_build_latency_ms",
        "generation_latency_ms",
        "end_to_end_latency_ms",
    )

    stage_metrics = {
        metric_name: _latency_summary(
            _numeric_metric_values(
                results,
                metric_name,
            )
        )
        for metric_name in stage_metric_names
    }

    return {
        "total_requests": total_requests,
        "successful_requests": successful_requests,
        "busy_requests": busy_requests,
        "status_counts": dict(
            sorted(status_codes.items())
        ),
        "classification_counts": dict(
            sorted(classifications.items())
        ),
        "success_rate": (
            successful_requests / total_requests
        ),
        "busy_rejection_rate": (
            busy_requests / total_requests
        ),
        "wall_time_ms": wall_time_ms,
        "completion_throughput_rps": (
            total_requests / wall_time_seconds
        ),
        "successful_throughput_rps": (
            successful_requests / wall_time_seconds
        ),
        "request_id_mismatches": (
            request_id_mismatches
        ),
        "client_latency_ms": {
            "all": _latency_summary(
                all_latencies
            ),
            "success": _latency_summary(
                success_latencies
            ),
            "busy": _latency_summary(
                busy_latencies
            ),
        },
        "server_stage_latency_ms": (
            stage_metrics
        ),
        "scheduler_launch_lag_ms": (
            _latency_summary(
                _numeric_result_values(
                    results,
                    "launch_lag_ms",
                )
            )
        ),
        "classification_sequence": (
            _classification_sequence(results)
        ),
        "error_details": (
            _error_details(results)
        ),
    }


def _print_latency(
    label: str,
    summary: dict[str, Any] | None,
) -> None:
    if summary is None:
        print(f"{label}: n/a")
        return

    print(
        f"{label}: "
        f"mean={summary['mean']:.2f}ms "
        f"p50={summary['p50']:.2f}ms "
        f"p95={summary['p95']:.2f}ms "
        f"p99={summary['p99']:.2f}ms"
    )


def _print_summary(
    summary: dict[str, Any],
) -> None:
    print()
    print("===== LOAD CHARACTERIZATION =====")
    print(
        "Requests: "
        f"{summary['total_requests']}"
    )
    print(
        "Status counts: "
        f"{summary['status_counts']}"
    )
    print(
        "Classifications: "
        f"{summary['classification_counts']}"
    )
    print(
        "Success rate: "
        f"{summary['success_rate']:.3f}"
    )
    print(
        "Busy rejection rate: "
        f"{summary['busy_rejection_rate']:.3f}"
    )
    print(
        "Wall time: "
        f"{summary['wall_time_ms']:.2f}ms"
    )

    if "target_rate_rps" in summary:
        print(
            "Target offered rate: "
            f"{summary['target_rate_rps']:.4f} req/s"
        )
        print(
            "Scheduled arrivals: "
            f"{summary['scheduled_requests']}"
        )
        print(
            "Scheduled arrival rate: "
            f"{summary['scheduled_arrival_rate_rps']:.4f} req/s"
        )

    print(
        "Completion throughput: "
        f"{summary['completion_throughput_rps']:.4f} req/s"
    )
    print(
        "Successful throughput: "
        f"{summary['successful_throughput_rps']:.4f} req/s"
    )
    print(
        "Request-ID mismatches: "
        f"{summary['request_id_mismatches']}"
    )

    client_latency = summary[
        "client_latency_ms"
    ]

    _print_latency(
        "Client latency — all",
        client_latency["all"],
    )
    _print_latency(
        "Client latency — success",
        client_latency["success"],
    )
    _print_latency(
        "Client latency — busy",
        client_latency["busy"],
    )

    for metric_name, metric_summary in (
        summary[
            "server_stage_latency_ms"
        ].items()
    ):
        _print_latency(
            f"Server {metric_name}",
            metric_summary,
        )

    _print_latency(
        "Scheduler launch lag",
        summary["scheduler_launch_lag_ms"],
    )

    sequence = summary[
        "classification_sequence"
    ]

    if len(sequence) <= 50:
        print(
            "Classification sequence: "
            + " -> ".join(sequence)
        )

    error_details = summary[
        "error_details"
    ]

    if error_details:
        print("Error details:")

        for error in error_details:
            print(
                "  "
                f"request={error['request_number']} "
                f"status={error['status_code']} "
                f"classification="
                f"{error['classification']} "
                f"latency_ms="
                f"{error['latency_ms']:.2f} "
                f"detail={error['detail']}"
            )


def _load_mode(
    args: argparse.Namespace,
) -> str:
    if args.rate_rps is not None:
        return "fixed_rate"

    if args.duration_seconds is not None:
        return "duration"

    return "request_count"


def _client_limits(
    args: argparse.Namespace,
    mode: str,
) -> httpx.Limits:
    if mode == "fixed_rate":
        return httpx.Limits(
            max_connections=None,
            max_keepalive_connections=20,
        )

    return httpx.Limits(
        max_connections=args.concurrency,
        max_keepalive_connections=args.concurrency,
    )


async def _main_async(
    args: argparse.Namespace,
) -> dict[str, Any]:
    base_url = args.base_url.rstrip("/")
    mode = _load_mode(args)

    run_id = datetime.now(
        timezone.utc
    ).strftime("%Y%m%dT%H%M%SZ")

    timeout = httpx.Timeout(
        args.timeout_seconds
    )
    limits = _client_limits(
        args,
        mode,
    )

    async with httpx.AsyncClient(
        timeout=timeout,
        limits=limits,
    ) as client:
        print("Checking readiness...")

        readiness = await client.get(
            f"{base_url}/ready"
        )

        if readiness.status_code != 200:
            raise RuntimeError(
                "API is not ready: "
                f"status={readiness.status_code} "
                f"body={readiness.text}"
            )

        print("API ready.")

        if args.warmup_requests > 0:
            await _run_warmup(
                client,
                base_url=base_url,
                query=args.query,
                run_id=run_id,
                warmup_requests=(
                    args.warmup_requests
                ),
            )

        arrival_offsets: list[float] | None = None

        if mode == "fixed_rate":
            print(
                "Starting fixed-rate workload: "
                f"duration_seconds="
                f"{args.duration_seconds} "
                f"rate_rps={args.rate_rps} "
                f"arrival_model="
                f"{args.arrival_model} "
                f"seed={args.seed}"
            )

            (
                results,
                wall_time_ms,
                arrival_offsets,
            ) = await _run_fixed_rate_requests(
                client,
                base_url=base_url,
                query=args.query,
                run_id=run_id,
                duration_seconds=(
                    args.duration_seconds
                ),
                rate_rps=args.rate_rps,
                arrival_model=args.arrival_model,
                seed=args.seed,
            )

        elif mode == "duration":
            print(
                "Starting sustained workload: "
                f"duration_seconds="
                f"{args.duration_seconds} "
                f"concurrency={args.concurrency}"
            )

            results, wall_time_ms = (
                await _run_sustained_requests(
                    client,
                    base_url=base_url,
                    query=args.query,
                    run_id=run_id,
                    duration_seconds=(
                        args.duration_seconds
                    ),
                    concurrency=args.concurrency,
                )
            )

        else:
            print(
                "Starting measured workload: "
                f"requests={args.requests} "
                f"concurrency={args.concurrency}"
            )

            results, wall_time_ms = (
                await _run_measured_requests(
                    client,
                    base_url=base_url,
                    query=args.query,
                    run_id=run_id,
                    request_count=args.requests,
                    concurrency=args.concurrency,
                )
            )

    summary = _build_summary(
        results,
        wall_time_ms,
    )

    if mode == "fixed_rate":
        scheduled_requests = len(
            arrival_offsets or []
        )

        summary["target_rate_rps"] = (
            args.rate_rps
        )
        summary["scheduled_requests"] = (
            scheduled_requests
        )
        summary[
            "scheduled_arrival_rate_rps"
        ] = (
            scheduled_requests
            / args.duration_seconds
        )

    return {
        "run_id": run_id,
        "timestamp_utc": datetime.now(
            timezone.utc
        ).isoformat(),
        "protocol": {
            "base_url": base_url,
            "endpoint": "/v1/query",
            "query": args.query,
            "mode": mode,
            "requests": args.requests,
            "duration_seconds": (
                args.duration_seconds
            ),
            "rate_rps": args.rate_rps,
            "arrival_model": (
                args.arrival_model
                if mode == "fixed_rate"
                else None
            ),
            "seed": (
                args.seed
                if (
                    mode == "fixed_rate"
                    and args.arrival_model
                    == "poisson"
                )
                else None
            ),
            "concurrency": (
                None
                if mode == "fixed_rate"
                else args.concurrency
            ),
            "warmup_requests": (
                args.warmup_requests
            ),
            "client_timeout_seconds": (
                args.timeout_seconds
            ),
            "load_model": (
                "open_loop"
                if mode == "fixed_rate"
                else "closed_loop"
            ),
        },
        "summary": summary,
        "requests": results,
    }


def _parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description=(
            "Characterize HTTP load behavior "
            "of the production RAG API."
        ),
        formatter_class=(
            argparse.ArgumentDefaultsHelpFormatter
        ),
    )

    parser.add_argument(
        "--base-url",
        default="http://localhost:8000",
    )
    parser.add_argument(
        "--query",
        default=DEFAULT_QUERY,
    )
    parser.add_argument(
        "--requests",
        type=int,
    )
    parser.add_argument(
        "--duration-seconds",
        type=float,
    )
    parser.add_argument(
        "--rate-rps",
        type=float,
    )
    parser.add_argument(
        "--arrival-model",
        choices=("fixed", "poisson"),
        default="fixed",
        help=(
            "Arrival schedule for fixed-rate mode. "
            "Used only with --rate-rps."
        ),
    )
    parser.add_argument(
        "--seed",
        type=int,
        default=DEFAULT_SEED,
        help=(
            "Deterministic random seed used by "
            "the Poisson arrival scheduler."
        ),
    )
    parser.add_argument(
        "--concurrency",
        type=int,
        default=1,
    )
    parser.add_argument(
        "--warmup-requests",
        type=int,
        default=1,
    )
    parser.add_argument(
        "--timeout-seconds",
        type=float,
        default=130.0,
    )
    parser.add_argument(
        "--output",
        type=Path,
    )

    args = parser.parse_args()

    if (
        args.requests is not None
        and args.duration_seconds is not None
    ):
        parser.error(
            "--requests and --duration-seconds "
            "cannot be used together"
        )

    if (
        args.rate_rps is not None
        and args.duration_seconds is None
    ):
        parser.error(
            "--rate-rps requires "
            "--duration-seconds"
        )

    if (
        args.rate_rps is not None
        and args.requests is not None
    ):
        parser.error(
            "--rate-rps cannot be used "
            "with --requests"
        )

    if (
        args.requests is None
        and args.duration_seconds is None
    ):
        args.requests = 3

    if (
        args.requests is not None
        and args.requests < 1
    ):
        parser.error(
            "--requests must be >= 1"
        )

    if (
        args.duration_seconds is not None
        and args.duration_seconds <= 0
    ):
        parser.error(
            "--duration-seconds must be > 0"
        )

    if (
        args.rate_rps is not None
        and args.rate_rps <= 0
    ):
        parser.error(
            "--rate-rps must be > 0"
        )

    if args.concurrency < 1:
        parser.error(
            "--concurrency must be >= 1"
        )

    if (
        args.requests is not None
        and args.concurrency > args.requests
    ):
        parser.error(
            "--concurrency must be <= "
            "--requests"
        )

    if args.warmup_requests < 0:
        parser.error(
            "--warmup-requests must be >= 0"
        )

    if args.timeout_seconds <= 0:
        parser.error(
            "--timeout-seconds must be > 0"
        )

    return args


def main() -> None:
    args = _parse_args()

    report = asyncio.run(
        _main_async(args)
    )

    _print_summary(
        report["summary"]
    )

    if args.output is not None:
        args.output.parent.mkdir(
            parents=True,
            exist_ok=True,
        )

        args.output.write_text(
            json.dumps(
                report,
                indent=2,
                ensure_ascii=False,
            )
            + "\n",
            encoding="utf-8",
        )

        print()
        print(
            f"Report written to: {args.output}"
        )


if __name__ == "__main__":
    main()