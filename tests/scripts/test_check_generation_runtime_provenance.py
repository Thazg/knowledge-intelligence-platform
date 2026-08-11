from __future__ import annotations

import json

import scripts.check_generation_runtime_provenance as cli


def test_main_returns_zero_when_runtime_provenance_matches(
    tmp_path,
    monkeypatch,
    capsys,
) -> None:
    manifest_path = tmp_path / "manifest.json"

    manifest_path.write_text(
        json.dumps(
            {
                "generator": {
                    "provider": "ollama",
                    "ollama_version": "0.32.5",
                    "model": "qwen3:4b-instruct",
                    "model_digest": "expected-digest",
                }
            }
        ),
        encoding="utf-8",
    )

    runtime = {
        "ollama_version": "0.32.5",
        "models": [
            {
                "name": "qwen3:4b-instruct",
                "digest": "expected-digest",
            }
        ],
    }

    monkeypatch.setattr(
        cli,
        "collect_generation_runtime",
        lambda **kwargs: runtime,
    )

    exit_code = cli.main(
        manifest_path=manifest_path
    )

    output = json.loads(
        capsys.readouterr().out
    )

    assert exit_code == 0
    assert output["verification"] == {
        "passed": True,
        "failures": [],
    }
    
def test_main_returns_one_when_runtime_provenance_mismatches(
    tmp_path,
    monkeypatch,
    capsys,
) -> None:
    manifest_path = tmp_path / "manifest.json"

    manifest_path.write_text(
        json.dumps(
            {
                "generator": {
                    "provider": "ollama",
                    "ollama_version": "0.32.5",
                    "model": "qwen3:4b-instruct",
                    "model_digest": "expected-digest",
                }
            }
        ),
        encoding="utf-8",
    )

    runtime = {
        "ollama_version": "0.32.5",
        "models": [
            {
                "name": "qwen3:4b-instruct",
                "digest": "wrong-digest",
            }
        ],
    }

    monkeypatch.setattr(
        cli,
        "collect_generation_runtime",
        lambda **kwargs: runtime,
    )

    exit_code = cli.main(
        manifest_path=manifest_path
    )

    output = json.loads(
        capsys.readouterr().out
    )

    assert exit_code == 1
    assert output["verification"]["passed"] is False

    assert {
        "type": "runtime_provenance",
        "field": "model_digest",
        "model": "qwen3:4b-instruct",
        "expected": "expected-digest",
        "actual": "wrong-digest",
    } in output["verification"]["failures"]