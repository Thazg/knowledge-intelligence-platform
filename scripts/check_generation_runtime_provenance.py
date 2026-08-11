from __future__ import annotations

import argparse
import json
from pathlib import Path

from backend.evaluation.generation_runtime import (
    collect_generation_runtime,
    fetch_ollama_tags,
    run_ollama_version_command,
)
from backend.evaluation.generation_runtime_provenance import (
    check_generation_runtime_provenance,
)


DEFAULT_MANIFEST_PATH = Path(
    "benchmarks/generation/v1/manifest.json"
)


def main(
    manifest_path: Path = DEFAULT_MANIFEST_PATH,
) -> int:
    manifest = json.loads(
        manifest_path.read_text(
            encoding="utf-8"
        )
    )

    runtime = collect_generation_runtime(
        run_version_command=(
            run_ollama_version_command
        ),
        fetch_tags=fetch_ollama_tags,
    )

    verification = (
        check_generation_runtime_provenance(
            manifest=manifest,
            runtime=runtime,
        )
    )

    print(
        json.dumps(
            {
                "runtime": runtime,
                "verification": verification,
            },
            indent=2,
        )
    )

    return 0 if verification["passed"] else 1


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description=(
            "Verify generation runtime provenance."
        )
    )

    parser.add_argument(
        "--manifest",
        type=Path,
        default=DEFAULT_MANIFEST_PATH,
        help=(
            "Generation benchmark manifest path."
        ),
    )

    return parser.parse_args()


if __name__ == "__main__":
    args = parse_args()

    raise SystemExit(
        main(
            manifest_path=args.manifest
        )
    )