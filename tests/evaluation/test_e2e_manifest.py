from __future__ import annotations

import hashlib
import json
import subprocess
from pathlib import Path


MANIFEST_PATH = Path(
    "benchmarks/e2e/v1/manifest.json"
)

FROZEN_MANIFEST_SHA256 = (
    "2190EDA38BB4E849E2A4FF84B97EF074"
    "36455861FC93F10D9D716377D2D194FE"
)


def _load_manifest() -> dict:
    return json.loads(
        MANIFEST_PATH.read_text(
            encoding="utf-8"
        )
    )


def _git_blob(path: str) -> bytes:
    return subprocess.check_output(
        [
            "git",
            "show",
            f"HEAD:{path}",
        ]
    )


def _sha256(data: bytes) -> str:
    return hashlib.sha256(
        data
    ).hexdigest().upper()


def _assert_sha256(value: str) -> None:
    assert len(value) == 64

    int(
        value,
        16,
    )


def test_e2e_manifest_v1_is_immutable() -> None:
    assert (
        _sha256(
            MANIFEST_PATH.read_bytes()
        )
        == FROZEN_MANIFEST_SHA256
    )


def test_e2e_manifest_freezes_benchmark_inputs() -> None:
    manifest = _load_manifest()

    assert (
        manifest["benchmark_version"]
        == "e2e_v1"
    )

    cases = manifest["cases"]

    assert cases["cases"] == 18

    assert (
        cases["sha256"]
        == _sha256(
            _git_blob(
                cases["path"]
            )
        )
    )

    retrieval = manifest[
        "retrieval_dependency"
    ]

    assert (
        retrieval["benchmark_version"]
        == "retrieval_full_v1"
    )

    assert (
        retrieval["sha256"]
        == _sha256(
            _git_blob(
                retrieval["manifest_path"]
            )
        )
    )


def test_e2e_manifest_freezes_retrieval_semantics() -> None:
    manifest = _load_manifest()

    retriever = manifest["retriever"]

    assert retriever["type"] == "weighted_rrf"
    assert retriever["dense_weight"] == 0.7
    assert retriever["bm25_weight"] == 0.3
    assert retriever["rrf_k"] == 60
    assert retriever["top_k"] == 10

    assert (
        retriever["candidate_multiplier"]
        == 5
    )

    assert (
        retriever[
            "max_chunks_per_document"
        ]
        == 1
    )

    _assert_sha256(
        retriever["source_sha256"]
    )


def test_e2e_manifest_freezes_deployment_config() -> None:
    manifest = _load_manifest()

    deployment = manifest["deployment"]

    assert (
        deployment["mode"]
        == "docker_compose"
    )

    _assert_sha256(
        deployment["compose_sha256"]
    )

    assert (
        deployment[
            "qdrant_image"
        ]["config_image"]
        == "qdrant/qdrant:v1.19.0"
    )


def test_e2e_manifest_freezes_rag_runtime_config() -> None:
    manifest = _load_manifest()

    vector_store = manifest[
        "vector_store"
    ]

    assert (
        vector_store["provider"]
        == "qdrant"
    )

    assert (
        vector_store["collection"]
        == (
            "enterprise_knowledge_"
            "fixed_bge_small"
        )
    )

    assert (
        vector_store["points_count"]
        == 36199
    )

    assert (
        vector_store["vector_size"]
        == 384
    )

    assert (
        vector_store["distance"]
        == "Cosine"
    )

    context = manifest["context"]

    assert (
        context["max_sources"]
        == 6
    )

    assert (
        context["max_context_tokens"]
        == 4000
    )

    generator = manifest["generator"]

    assert (
        generator["provider"]
        == "ollama"
    )

    assert (
        generator["model"]
        == "qwen3:4b-instruct"
    )

    assert (
        generator["temperature"]
        == 0.0
    )

    assert (
        generator["num_predict"]
        == 384
    )

    assert (
        generator["timeout_seconds"]
        == 120.0
    )

    _assert_sha256(
        generator["source_sha256"]
    )


def test_e2e_manifest_freezes_prompt_v3() -> None:
    manifest = _load_manifest()

    prompt = manifest["prompt"]

    assert (
        prompt["version"]
        == "v3"
    )

    assert (
        prompt[
            "fingerprint_strategy"
        ]
        == "canonical_prompt_ast_v1"
    )

    _assert_sha256(
        prompt["sha256"]
    )


def test_e2e_manifest_freezes_execution_protocol() -> None:
    manifest = _load_manifest()

    protocol = manifest[
        "execution_protocol"
    ]

    assert (
        protocol["transport"]
        == "http"
    )

    assert (
        protocol["readiness_required"]
        is True
    )

    assert (
        protocol["warmup_requests"]
        == 1
    )

    assert (
        protocol[
            "measured_requests_per_case"
        ]
        == 1
    )

    assert (
        protocol["case_order"]
        == "cases_file_order"
    )

    assert (
        protocol["concurrency"]
        == 1
    )

    assert (
        protocol["measurement_mode"]
        == "steady_state"
    )

    assert (
        protocol[
            "http_round_trip_latency"
        ]
        == (
            "measured_client_side_"
            "separately"
        )
    )


def test_e2e_manifest_freezes_runner_and_runtime_environment() -> None:
    manifest = _load_manifest()

    runner = manifest[
        "benchmark_runner"
    ]

    assert (
        runner["source_path"]
        == "scripts/evaluate_e2e_v1.py"
    )

    _assert_sha256(
        runner["source_sha256"]
    )

    assert (
        runner[
            "fail_fast_on_runtime_failure"
        ]
        is True
    )

    runtime = manifest[
        "runtime_environment"
    ]

    assert (
        runtime["host_total_ram_gib"]
        == 15.77
    )

    assert (
        runtime["wsl2_memory_config"]
        == "10GB"
    )

    assert (
        runtime[
            "docker_total_memory_gib_observed"
        ]
        == 9.712
    )

    protocol = manifest[
        "execution_protocol"
    ]

    assert (
        protocol[
            "fail_fast_on_runtime_failure"
        ]
        is True
    )