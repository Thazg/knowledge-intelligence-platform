from __future__ import annotations

import re
import subprocess
import httpx
from collections.abc import Callable

def parse_ollama_version(output: str) -> str:
    match = re.search(
        r"ollama version is\s+([^\s]+)",
        output,
        flags=re.IGNORECASE,
    )

    if match is None:
        raise ValueError(
            "Unable to parse Ollama version"
        )

    return match.group(1)

def normalize_ollama_models(
    payload: dict,
) -> list[dict]:
    return [
        {
            "name": model["name"],
            "digest": model["digest"],
        }
        for model in payload.get("models", [])
    ]
    
def collect_generation_runtime(
    run_version_command: Callable[[], str],
    fetch_tags: Callable[[], dict],
) -> dict:
    version_output = run_version_command()
    tags_payload = fetch_tags()

    return {
        "ollama_version": parse_ollama_version(
            version_output
        ),
        "models": normalize_ollama_models(
            tags_payload
        ),
    }
    
def run_ollama_version_command() -> str:
    completed = subprocess.run(
        [
            "ollama",
            "--version",
        ],
        capture_output=True,
        text=True,
        check=True,
    )

    return completed.stdout

def fetch_ollama_tags() -> dict:
    response = httpx.get(
        "http://localhost:11434/api/tags",
        timeout=10.0,
    )

    response.raise_for_status()

    return response.json()