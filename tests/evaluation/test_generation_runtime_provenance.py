from __future__ import annotations

from backend.evaluation.generation_runtime_provenance import (
    check_generation_runtime_provenance,
)


def test_generation_runtime_provenance_passes_when_runtime_matches() -> None:
    manifest = {
        "generator": {
            "provider": "ollama",
            "ollama_version": "0.32.5",
            "model": "qwen3:4b-instruct",
            "model_digest": (
                "0edcdef34593eac1aa2be9c7d06c432d"
                "cf81945adca5eca2f27662c18f168ba0"
            ),
        }
    }

    runtime = {
        "ollama_version": "0.32.5",
        "models": [
            {
                "name": "qwen3:4b-instruct",
                "digest": (
                    "0edcdef34593eac1aa2be9c7d06c432d"
                    "cf81945adca5eca2f27662c18f168ba0"
                ),
            }
        ],
    }

    result = check_generation_runtime_provenance(
        manifest=manifest,
        runtime=runtime,
    )

    assert result == {
        "passed": True,
        "failures": [],
    }
    
def test_generation_runtime_provenance_fails_on_wrong_ollama_version() -> None:
    manifest = {
        "generator": {
            "provider": "ollama",
            "ollama_version": "0.32.5",
            "model": "qwen3:4b-instruct",
            "model_digest": "expected-digest",
        }
    }

    runtime = {
        "ollama_version": "0.31.0",
        "models": [
            {
                "name": "qwen3:4b-instruct",
                "digest": "expected-digest",
            }
        ],
    }

    result = check_generation_runtime_provenance(
        manifest=manifest,
        runtime=runtime,
    )

    assert result["passed"] is False

    assert {
        "type": "runtime_provenance",
        "field": "ollama_version",
        "expected": "0.32.5",
        "actual": "0.31.0",
    } in result["failures"]


def test_generation_runtime_provenance_fails_when_model_is_missing() -> None:
    manifest = {
        "generator": {
            "provider": "ollama",
            "ollama_version": "0.32.5",
            "model": "qwen3:4b-instruct",
            "model_digest": "expected-digest",
        }
    }

    runtime = {
        "ollama_version": "0.32.5",
        "models": [],
    }

    result = check_generation_runtime_provenance(
        manifest=manifest,
        runtime=runtime,
    )

    assert result["passed"] is False

    assert {
        "type": "runtime_provenance",
        "field": "model",
        "expected": "qwen3:4b-instruct",
        "actual": None,
    } in result["failures"]


def test_generation_runtime_provenance_fails_on_wrong_model_digest() -> None:
    manifest = {
        "generator": {
            "provider": "ollama",
            "ollama_version": "0.32.5",
            "model": "qwen3:4b-instruct",
            "model_digest": "expected-digest",
        }
    }

    runtime = {
        "ollama_version": "0.32.5",
        "models": [
            {
                "name": "qwen3:4b-instruct",
                "digest": "wrong-digest",
            }
        ],
    }

    result = check_generation_runtime_provenance(
        manifest=manifest,
        runtime=runtime,
    )

    assert result["passed"] is False

    assert {
        "type": "runtime_provenance",
        "field": "model_digest",
        "model": "qwen3:4b-instruct",
        "expected": "expected-digest",
        "actual": "wrong-digest",
    } in result["failures"]