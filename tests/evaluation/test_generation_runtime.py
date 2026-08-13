from __future__ import annotations

from backend.evaluation.generation_runtime import (
    collect_generation_runtime,
    fetch_ollama_tags,
    normalize_ollama_models,
    parse_ollama_version,
    run_ollama_version_command,
)


def test_parse_ollama_version() -> None:
    version = parse_ollama_version(
        "ollama version is 0.32.5\n"
    )

    assert version == "0.32.5"

def test_normalize_ollama_models() -> None:
    payload = {
        "models": [
            {
                "name": "qwen3:4b-instruct",
                "model": "qwen3:4b-instruct",
                "modified_at": "2026-07-01T00:00:00Z",
                "size": 2497293803,
                "digest": (
                    "0edcdef34593eac1aa2be9c7d06c432d"
                    "cf81945adca5eca2f27662c18f168ba0"
                ),
                "details": {
                    "format": "gguf",
                    "family": "qwen3",
                    "parameter_size": "4.0B",
                    "quantization_level": "Q4_K_M",
                },
            }
        ]
    }

    models = normalize_ollama_models(payload)

    assert models == [
        {
            "name": "qwen3:4b-instruct",
            "digest": (
                "0edcdef34593eac1aa2be9c7d06c432d"
                "cf81945adca5eca2f27662c18f168ba0"
            ),
        }
    ]
    
def test_collect_generation_runtime() -> None:
    def fake_run_command() -> str:
        return "ollama version is 0.32.5\n"

    def fake_fetch_tags() -> dict:
        return {
            "models": [
                {
                    "name": "qwen3:4b-instruct",
                    "digest": "model-digest",
                    "size": 2497293803,
                }
            ]
        }

    runtime = collect_generation_runtime(
        run_version_command=fake_run_command,
        fetch_tags=fake_fetch_tags,
    )

    assert runtime == {
        "ollama_version": "0.32.5",
        "models": [
            {
                "name": "qwen3:4b-instruct",
                "digest": "model-digest",
            }
        ],
    }
def test_run_ollama_version_command(
    monkeypatch,
) -> None:
    class FakeCompletedProcess:
        stdout = "ollama version is 0.32.5\n"

    def fake_run(*args, **kwargs):
        assert args[0] == [
            "ollama",
            "--version",
        ]
        assert kwargs["capture_output"] is True
        assert kwargs["text"] is True
        assert kwargs["check"] is True

        return FakeCompletedProcess()

    monkeypatch.setattr(
        "backend.evaluation.generation_runtime.subprocess.run",
        fake_run,
    )

    output = run_ollama_version_command()

    assert output == "ollama version is 0.32.5\n"
    
def test_fetch_ollama_tags(
    monkeypatch,
) -> None:
    class FakeResponse:
        def raise_for_status(self) -> None:
            return None

        def json(self) -> dict:
            return {
                "models": [
                    {
                        "name": "qwen3:4b-instruct",
                        "digest": "model-digest",
                    }
                ]
            }

    def fake_get(*args, **kwargs):
        assert args[0] == (
            "http://localhost:11434/api/tags"
        )
        assert kwargs["timeout"] == 10.0

        return FakeResponse()

    monkeypatch.setattr(
        "backend.evaluation.generation_runtime.httpx.get",
        fake_get,
    )

    payload = fetch_ollama_tags()

    assert payload == {
        "models": [
            {
                "name": "qwen3:4b-instruct",
                "digest": "model-digest",
            }
        ]
    }

def test_run_ollama_version_command_accepts_custom_command(
    monkeypatch,
) -> None:
    class FakeCompletedProcess:
        stdout = "ollama version is 0.32.5\n"

    def fake_run(*args, **kwargs):
        assert args[0] == [
            "docker",
            "exec",
            "enterprise-rag-ollama",
            "ollama",
            "--version",
        ]
        assert kwargs["capture_output"] is True
        assert kwargs["text"] is True
        assert kwargs["check"] is True

        return FakeCompletedProcess()

    monkeypatch.setattr(
        "backend.evaluation.generation_runtime.subprocess.run",
        fake_run,
    )

    output = run_ollama_version_command(
        command=[
            "docker",
            "exec",
            "enterprise-rag-ollama",
            "ollama",
            "--version",
        ]
    )

    assert output == "ollama version is 0.32.5\n"


def test_fetch_ollama_tags_accepts_custom_base_url(
    monkeypatch,
) -> None:
    class FakeResponse:
        def raise_for_status(self) -> None:
            return None

        def json(self) -> dict:
            return {
                "models": [
                    {
                        "name": "qwen3:4b-instruct",
                        "digest": "model-digest",
                    }
                ]
            }

    def fake_get(*args, **kwargs):
        assert args[0] == (
            "http://localhost:11435/api/tags"
        )
        assert kwargs["timeout"] == 10.0

        return FakeResponse()

    monkeypatch.setattr(
        "backend.evaluation.generation_runtime.httpx.get",
        fake_get,
    )

    payload = fetch_ollama_tags(
        base_url="http://localhost:11435",
    )

    assert payload["models"][0]["digest"] == "model-digest"