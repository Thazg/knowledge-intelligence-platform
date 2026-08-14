from __future__ import annotations

import ast
import hashlib
import json
import subprocess
from pathlib import Path


MANIFEST_PATH = Path("benchmarks/e2e/v1/manifest.json")


def _load_manifest() -> dict:
    return json.loads(
        MANIFEST_PATH.read_text(encoding="utf-8")
    )


def _git_blob(path: str) -> bytes:
    return subprocess.check_output(
        ["git", "show", f"HEAD:{path}"]
    )


def _sha256(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest().upper()


def _prompt_fingerprint(path: str) -> str:
    source = _git_blob(path).decode("utf-8")
    tree = ast.parse(source)

    prompt_builder = next(
        node
        for node in tree.body
        if isinstance(node, ast.ClassDef)
        and node.name == "PromptBuilder"
    )

    system_prompt = None
    templates: dict[str, str] = {}

    for node in prompt_builder.body:
        if isinstance(node, ast.Assign):
            for target in node.targets:
                if (
                    isinstance(target, ast.Name)
                    and target.id == "SYSTEM_PROMPT"
                ):
                    system_prompt = ast.literal_eval(
                        node.value
                    )

        if (
            isinstance(
                node,
                (ast.FunctionDef, ast.AsyncFunctionDef),
            )
            and node.name
            in {
                "_build_user_prompt",
                "_build_no_context_prompt",
            }
        ):
            return_node = next(
                child
                for child in ast.walk(node)
                if isinstance(child, ast.Return)
            )

            templates[node.name] = ast.dump(
                return_node.value,
                annotate_fields=True,
                include_attributes=False,
            )

    assert system_prompt is not None

    assert set(templates) == {
        "_build_user_prompt",
        "_build_no_context_prompt",
    }

    canonical = {
        "system_prompt": system_prompt,
        "templates": templates,
    }

    canonical_bytes = json.dumps(
        canonical,
        ensure_ascii=False,
        sort_keys=True,
        separators=(",", ":"),
    ).encode("utf-8")

    return _sha256(canonical_bytes)


def test_e2e_manifest_freezes_benchmark_inputs() -> None:
    manifest = _load_manifest()

    assert manifest["benchmark_version"] == "e2e_v1"

    cases = manifest["cases"]
    assert cases["cases"] == 18
    assert cases["sha256"] == _sha256(
        _git_blob(cases["path"])
    )

    retrieval = manifest["retrieval_dependency"]
    assert (
        retrieval["benchmark_version"]
        == "retrieval_full_v1"
    )
    assert retrieval["sha256"] == _sha256(
        _git_blob(retrieval["manifest_path"])
    )


def test_e2e_manifest_freezes_retrieval_semantics() -> None:
    manifest = _load_manifest()

    retriever = manifest["retriever"]

    assert retriever["type"] == "weighted_rrf"
    assert retriever["dense_weight"] == 0.7
    assert retriever["bm25_weight"] == 0.3
    assert retriever["rrf_k"] == 60
    assert retriever["top_k"] == 10
    assert retriever["candidate_multiplier"] == 5
    assert retriever["max_chunks_per_document"] == 1

    assert retriever["source_sha256"] == _sha256(
        _git_blob(retriever["source_path"])
    )


def test_e2e_manifest_freezes_deployment_config() -> None:
    manifest = _load_manifest()

    deployment = manifest["deployment"]

    assert deployment["mode"] == "docker_compose"

    assert deployment["compose_sha256"] == _sha256(
        _git_blob(deployment["compose_path"])
    )

    assert (
        deployment["qdrant_image"]["config_image"]
        == "qdrant/qdrant:v1.19.0"
    )


def test_e2e_manifest_freezes_rag_runtime_config() -> None:
    manifest = _load_manifest()

    vector_store = manifest["vector_store"]
    assert vector_store["provider"] == "qdrant"
    assert (
        vector_store["collection"]
        == "enterprise_knowledge_fixed_bge_small"
    )
    assert vector_store["points_count"] == 36199
    assert vector_store["vector_size"] == 384
    assert vector_store["distance"] == "Cosine"

    context = manifest["context"]
    assert context["max_sources"] == 6
    assert context["max_context_tokens"] == 4000

    generator = manifest["generator"]
    assert generator["provider"] == "ollama"
    assert generator["model"] == "qwen3:4b-instruct"
    assert generator["temperature"] == 0.0
    assert generator["num_predict"] == 384
    assert generator["timeout_seconds"] == 120.0

    assert generator["source_sha256"] == _sha256(
        _git_blob(generator["source_path"])
    )


def test_e2e_manifest_freezes_prompt_v3() -> None:
    manifest = _load_manifest()

    prompt = manifest["prompt"]

    assert prompt["version"] == "v3"
    assert (
        prompt["fingerprint_strategy"]
        == "canonical_prompt_ast_v1"
    )

    assert prompt["sha256"] == _prompt_fingerprint(
        prompt["source_path"]
    )


def test_e2e_manifest_freezes_execution_protocol() -> None:
    manifest = _load_manifest()

    protocol = manifest["execution_protocol"]

    assert protocol["transport"] == "http"
    assert protocol["readiness_required"] is True
    assert protocol["warmup_requests"] == 1
    assert protocol["measured_requests_per_case"] == 1
    assert protocol["case_order"] == "cases_file_order"
    assert protocol["concurrency"] == 1
    assert protocol["measurement_mode"] == "steady_state"
    assert (
        protocol["http_round_trip_latency"]
        == "measured_client_side_separately"
    )
