from __future__ import annotations

import ast
import hashlib
import json
import subprocess
from pathlib import Path


MANIFEST_PATH = Path(
    "benchmarks/generation/v1/manifest.json"
)


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
                (
                    ast.FunctionDef,
                    ast.AsyncFunctionDef,
                ),
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

    canonical_prompt = {
        "system_prompt": system_prompt,
        "templates": templates,
    }

    canonical_bytes = json.dumps(
        canonical_prompt,
        ensure_ascii=False,
        sort_keys=True,
        separators=(",", ":"),
    ).encode("utf-8")

    return _sha256(canonical_bytes)


def test_generation_manifest_matches_frozen_provenance() -> None:
    manifest = _load_manifest()

    assert manifest["benchmark_version"] == "generation_v1"

    cases = manifest["cases"]

    assert cases["cases"] == 12
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

    prompt = manifest["prompt"]

    assert prompt["version"] == "v3"

    assert (
        prompt["fingerprint_strategy"]
        == "canonical_prompt_ast_v1"
    )

    assert prompt["sha256"] == _prompt_fingerprint(
        prompt["source_path"]
    )


def test_generation_manifest_freezes_runtime_and_policy() -> None:
    manifest = _load_manifest()

    assert manifest["retriever"] == {
        "type": "weighted_rrf",
        "dense_weight": 0.7,
        "bm25_weight": 0.3,
        "rrf_k": 60,
        "top_k": 10,
    }

    assert manifest["context"] == {
        "max_sources": 6,
        "max_context_tokens": 4000,
    }

    assert manifest["generator"] == {
        "provider": "ollama",
        "ollama_version": "0.32.5",
        "model": "qwen3:4b-instruct",
        "model_digest": (
            "0edcdef34593eac1aa2be9c7d06c432d"
            "cf81945adca5eca2f27662c18f168ba0"
        ),
        "temperature": 0.0,
        "num_predict": 384,
    }

    hard_gates = manifest["regression"]["hard_gates"]

    assert hard_gates["case_integrity"] == {
        "expected_case_count": 12,
        "result_record_count": 12,
        "missing_case_ids": [],
        "duplicate_case_ids": [],
        "unknown_case_ids": [],
    }

    assert hard_gates["execution"] == {
        "generation_failure_count": 0,
        "empty_answer_count": 0,
    }

    assert hard_gates["citations"] == {
        "total_invalid_citation_count": 0,
    }

    assert hard_gates["evidence"] == {
        "missing_evidence_case_count": 0,
    }

    assert hard_gates["result_integrity"] == {
        "citation_source_mapping_error_count": 0,
        "duplicate_source_citation_id_count": 0,
    }

    format_policy = manifest[
        "regression"
    ]["tolerance_gates"][
        "citation_format_violations"
    ]

    assert format_policy["maximum_count"] == 2
    assert format_policy["allowed_case_ids"] == [
        "gen-009"
    ]

    baseline = manifest["approved_baseline"]

    assert baseline["citations"][
        "total_raw_citation_count"
    ] == 82

    assert baseline["citations"][
        "total_valid_citation_count"
    ] == 82

    assert baseline["citations"][
        "total_invalid_citation_count"
    ] == 0

    assert baseline["citations"][
        "total_citation_format_violation_count"
    ] == 2

    assert baseline["citations"][
        "citation_format_violation_case_ids"
    ] == ["gen-009"]

    assert baseline["evidence"][
        "missing_evidence_case_count"
    ] == 0

    assert baseline["result_integrity"][
        "citation_source_mapping_error_count"
    ] == 0

    assert baseline["result_integrity"][
        "duplicate_source_citation_id_count"
    ] == 0