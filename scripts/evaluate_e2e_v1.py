from __future__ import annotations

import argparse
import json
import time
from pathlib import Path
from typing import Any

import httpx


DEFAULT_MANIFEST_PATH = Path(
    "benchmarks/e2e/v1/manifest.json"
)

DEFAULT_OUTPUT_PATH = Path(
    "benchmarks/e2e/results_v1.jsonl"
)


def load_json(path: Path) -> dict:
    return json.loads(
        path.read_text(encoding="utf-8")
    )


def load_cases(path: Path) -> list[dict]:
    cases: list[dict] = []

    with path.open(
        "r",
        encoding="utf-8",
    ) as file:
        for line_number, line in enumerate(
            file,
            start=1,
        ):
            line = line.strip()

            if not line:
                continue

            try:
                record = json.loads(line)
            except json.JSONDecodeError as exc:
                raise ValueError(
                    f"Invalid JSON at line "
                    f"{line_number}: {exc}"
                ) from exc

            cases.append(record)

    return cases


def validate_readiness_payload(
    payload: dict,
) -> None:
    if payload.get("status") != "ready":
        raise RuntimeError(
            "API readiness status is not ready: "
            f"{payload!r}"
        )

    dependencies = payload.get(
        "dependencies",
        {},
    )

    unavailable = sorted(
        name
        for name, status
        in dependencies.items()
        if status != "ready"
    )

    if unavailable:
        raise RuntimeError(
            "API dependencies are not ready: "
            + ", ".join(unavailable)
        )


def build_success_record(
    *,
    case: dict,
    status_code: int,
    request_id_sent: str,
    request_id_received: str | None,
    http_round_trip_latency_ms: float,
    payload: dict[str, Any],
) -> dict:
    metrics = payload.get("metrics") or {}

    return {
        "case_id": case["case_id"],
        "category": case["category"],
        "query": case["query"],
        "expected_behavior": (
            case["expected_behavior"]
        ),
        "tags": case.get("tags", []),
        "notes": case.get("notes"),

        "http_status": status_code,
        "request_id_sent": request_id_sent,
        "request_id_received": (
            request_id_received
        ),
        "http_round_trip_latency_ms": (
            http_round_trip_latency_ms
        ),

        "answer": payload.get("answer", ""),
        "citations": payload.get(
            "citations",
            [],
        ),
        "sources": payload.get(
            "sources",
            [],
        ),
        "model": payload.get("model"),

        "retrieval_latency_ms": metrics.get(
            "retrieval_latency_ms"
        ),
        "context_build_latency_ms": metrics.get(
            "context_build_latency_ms"
        ),
        "generation_latency_ms": metrics.get(
            "generation_latency_ms"
        ),
        "end_to_end_latency_ms": metrics.get(
            "end_to_end_latency_ms"
        ),

        # Preserve the exact user-facing API payload
        # for later audit/debugging.
        "response_json": payload,
    }


def build_error_record(
    *,
    case: dict,
    error: str,
    message: str,
    request_id_sent: str,
    http_round_trip_latency_ms: float,
    status_code: int | None = None,
    request_id_received: str | None = None,
    response_body: Any = None,
) -> dict:
    return {
        "case_id": case["case_id"],
        "category": case["category"],
        "query": case["query"],
        "expected_behavior": (
            case["expected_behavior"]
        ),
        "tags": case.get("tags", []),
        "notes": case.get("notes"),

        "error": error,
        "message": message,

        "http_status": status_code,
        "request_id_sent": request_id_sent,
        "request_id_received": (
            request_id_received
        ),
        "http_round_trip_latency_ms": (
            http_round_trip_latency_ms
        ),
        "response_body": response_body,
    }


def append_jsonl(
    path: Path,
    record: dict,
) -> None:
    with path.open(
        "a",
        encoding="utf-8",
    ) as file:
        file.write(
            json.dumps(
                record,
                ensure_ascii=False,
            )
        )
        file.write("\n")


def request_id_for_case(
    benchmark_version: str,
    case_id: str,
) -> str:
    return (
        f"{benchmark_version}-{case_id}"
    )


def run_warmup(
    *,
    client: httpx.Client,
    endpoint_url: str,
    request_id_header: str,
    benchmark_version: str,
    warmup_query: str,
    warmup_requests: int,
) -> None:
    for index in range(
        1,
        warmup_requests + 1,
    ):
        request_id = (
            f"{benchmark_version}-"
            f"warmup-{index}"
        )

        response = client.post(
            endpoint_url,
            json={
                "query": warmup_query,
            },
            headers={
                request_id_header: request_id,
            },
        )

        if response.status_code != 200:
            raise RuntimeError(
                "Warmup request failed with "
                f"HTTP {response.status_code}: "
                f"{response.text}"
            )

        echoed_request_id = (
            response.headers.get(
                request_id_header
            )
        )

        if echoed_request_id != request_id:
            raise RuntimeError(
                "Warmup request ID mismatch: "
                f"sent={request_id!r}, "
                f"received={echoed_request_id!r}"
            )


def run_case(
    *,
    client: httpx.Client,
    endpoint_url: str,
    request_id_header: str,
    benchmark_version: str,
    case: dict,
) -> dict:
    request_id = request_id_for_case(
        benchmark_version,
        case["case_id"],
    )

    start = time.perf_counter()

    try:
        response = client.post(
            endpoint_url,
            json={
                "query": case["query"],
            },
            headers={
                request_id_header: request_id,
            },
        )

    except httpx.RequestError as exc:
        latency_ms = (
            time.perf_counter() - start
        ) * 1000

        return build_error_record(
            case=case,
            error=type(exc).__name__,
            message=str(exc),
            request_id_sent=request_id,
            http_round_trip_latency_ms=(
                latency_ms
            ),
        )

    latency_ms = (
        time.perf_counter() - start
    ) * 1000

    received_request_id = (
        response.headers.get(
            request_id_header
        )
    )

    if response.status_code != 200:
        try:
            response_body: Any = (
                response.json()
            )
        except ValueError:
            response_body = response.text

        return build_error_record(
            case=case,
            error="UnexpectedHTTPStatus",
            message=(
                "Expected HTTP 200, got "
                f"{response.status_code}"
            ),
            request_id_sent=request_id,
            request_id_received=(
                received_request_id
            ),
            http_round_trip_latency_ms=(
                latency_ms
            ),
            status_code=response.status_code,
            response_body=response_body,
        )

    try:
        payload = response.json()
    except ValueError as exc:
        return build_error_record(
            case=case,
            error="InvalidJSONResponse",
            message=str(exc),
            request_id_sent=request_id,
            request_id_received=(
                received_request_id
            ),
            http_round_trip_latency_ms=(
                latency_ms
            ),
            status_code=response.status_code,
            response_body=response.text,
        )

    return build_success_record(
        case=case,
        status_code=response.status_code,
        request_id_sent=request_id,
        request_id_received=(
            received_request_id
        ),
        http_round_trip_latency_ms=(
            latency_ms
        ),
        payload=payload,
    )


def main(
    *,
    manifest_path: Path = (
        DEFAULT_MANIFEST_PATH
    ),
    output_path: Path = (
        DEFAULT_OUTPUT_PATH
    ),
    case_id: str | None = None,
) -> None:
    manifest = load_json(
        manifest_path
    )

    benchmark_version = manifest[
        "benchmark_version"
    ]

    api_config = manifest["api"]
    protocol = manifest[
        "execution_protocol"
    ]

    base_url = api_config[
        "base_url"
    ].rstrip("/")

    endpoint_url = (
        f"{base_url}"
        f"{api_config['endpoint']}"
    )

    readiness_url = (
        f"{base_url}"
        f"{api_config['readiness_endpoint']}"
    )

    request_id_header = api_config[
        "request_id_header"
    ]

    timeout_seconds = float(
        protocol[
            "http_client_timeout_seconds"
        ]
    )

    cases_path = Path(
        manifest["cases"]["path"]
    )

    cases = load_cases(
        cases_path
    )

    expected_case_count = int(
        manifest["cases"]["cases"]
    )

    if len(cases) != expected_case_count:
        raise RuntimeError(
            "Case count does not match "
            "manifest: "
            f"expected={expected_case_count}, "
            f"actual={len(cases)}"
        )

    if case_id is not None:
        if output_path == DEFAULT_OUTPUT_PATH:
            raise ValueError(
                "--case-id requires a "
                "non-canonical --output path"
            )

        selected = [
            case
            for case in cases
            if case["case_id"] == case_id
        ]

        if len(selected) != 1:
            raise ValueError(
                f"Unknown case_id: {case_id}"
            )

        cases = selected

    print(
        f"Loaded {len(cases)} E2E case(s)."
    )
    print(
        f"Endpoint: {endpoint_url}"
    )

    with httpx.Client(
        timeout=timeout_seconds,
    ) as client:
        print("Checking readiness...")

        readiness_response = client.get(
            readiness_url
        )

        readiness_response.raise_for_status()

        readiness_payload = (
            readiness_response.json()
        )

        validate_readiness_payload(
            readiness_payload
        )

        print("Readiness: OK")

        warmup_requests = int(
            protocol["warmup_requests"]
        )

        if warmup_requests > 0:
            print(
                f"Running "
                f"{warmup_requests} warmup "
                f"request(s)..."
            )

            run_warmup(
                client=client,
                endpoint_url=endpoint_url,
                request_id_header=(
                    request_id_header
                ),
                benchmark_version=(
                    benchmark_version
                ),
                warmup_query=protocol[
                    "warmup_query"
                ],
                warmup_requests=(
                    warmup_requests
                ),
            )

            print("Warmup: OK")

        output_path.parent.mkdir(
            parents=True,
            exist_ok=True,
        )

        # Only truncate output after
        # readiness + warmup succeed.
        output_path.write_text(
            "",
            encoding="utf-8",
        )

        benchmark_start = (
            time.perf_counter()
        )

        print()
        print(
            "Starting E2E HTTP benchmark..."
        )
        print()

        for index, case in enumerate(
            cases,
            start=1,
        ):
            print(
                f"[{index:>2}/{len(cases)}] "
                f"{case['case_id']} | "
                f"{case['category']}"
            )

            record = run_case(
                client=client,
                endpoint_url=endpoint_url,
                request_id_header=(
                    request_id_header
                ),
                benchmark_version=(
                    benchmark_version
                ),
                case=case,
            )

            append_jsonl(
                output_path,
                record,
            )

            if "error" in record:
                print(
                    f"     ERROR: "
                    f"{record['error']} | "
                    f"{record['message']}"
                )
            else:
                print(
                    "     HTTP round-trip: "
                    f"{record['http_round_trip_latency_ms']:.2f} ms"
                )

                print(
                    "     Pipeline E2E: "
                    f"{record['end_to_end_latency_ms']:.2f} ms"
                )

                print(
                    "     Sources: "
                    f"{len(record['sources'])} | "
                    "API citations: "
                    f"{len(record['citations'])}"
                )

            print()

    total_seconds = (
        time.perf_counter()
        - benchmark_start
    )

    print("=" * 64)
    print("E2E HTTP BENCHMARK COMPLETE")
    print("=" * 64)
    print(
        f"Cases: {len(cases)}"
    )
    print(
        "Total time: "
        f"{total_seconds / 60:.2f} min"
    )
    print(
        f"Results: {output_path}"
    )


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description=(
            "Run E2E RAG validation v1 "
            "through the public HTTP API."
        ),
    )

    parser.add_argument(
        "--manifest",
        type=Path,
        default=DEFAULT_MANIFEST_PATH,
    )

    parser.add_argument(
        "--output",
        type=Path,
        default=DEFAULT_OUTPUT_PATH,
    )

    parser.add_argument(
        "--case-id",
        default=None,
        help=(
            "Run one case for smoke testing. "
            "Requires a non-canonical "
            "--output path."
        ),
    )

    return parser.parse_args()


if __name__ == "__main__":
    args = parse_args()

    main(
        manifest_path=args.manifest,
        output_path=args.output,
        case_id=args.case_id,
    )
