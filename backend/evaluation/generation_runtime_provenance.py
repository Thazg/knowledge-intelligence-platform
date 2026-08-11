from __future__ import annotations


def check_generation_runtime_provenance(
    manifest: dict,
    runtime: dict,
) -> dict:
    failures: list[dict] = []

    expected_generator = manifest["generator"]

    expected_ollama_version = expected_generator[
        "ollama_version"
    ]

    actual_ollama_version = runtime[
        "ollama_version"
    ]

    if actual_ollama_version != expected_ollama_version:
        failures.append(
            {
                "type": "runtime_provenance",
                "field": "ollama_version",
                "expected": expected_ollama_version,
                "actual": actual_ollama_version,
            }
        )

    expected_model_name = expected_generator[
        "model"
    ]

    expected_model_digest = expected_generator[
        "model_digest"
    ]

    model_by_name = {
        model["name"]: model
        for model in runtime.get("models", [])
    }

    actual_model = model_by_name.get(
        expected_model_name
    )

    if actual_model is None:
        failures.append(
            {
                "type": "runtime_provenance",
                "field": "model",
                "expected": expected_model_name,
                "actual": None,
            }
        )
    else:
        actual_model_digest = actual_model.get(
            "digest"
        )

        if (
            actual_model_digest
            != expected_model_digest
        ):
            failures.append(
                {
                    "type": "runtime_provenance",
                    "field": "model_digest",
                    "model": expected_model_name,
                    "expected": expected_model_digest,
                    "actual": actual_model_digest,
                }
            )

    return {
        "passed": not failures,
        "failures": failures,
    }