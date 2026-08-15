from __future__ import annotations

import hashlib
import json
from pathlib import Path
from typing import Any

from backend.chunking.serializer import ChunkSerializer


CASES_PATH = Path(
    "benchmarks/e2e/cases_v1.jsonl"
)

RESULTS_PATH = Path(
    "benchmarks/e2e/results_v1.jsonl"
)

CHUNKS_PATH = Path(
    "data/processed/chunks_fixed.jsonl"
)

OUTPUT_PATH = Path(
    "benchmarks/e2e/review/human_review_packet_v1.md"
)


def load_jsonl(path: Path) -> list[dict]:
    records: list[dict] = []

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
                records.append(
                    json.loads(line)
                )
            except json.JSONDecodeError as exc:
                raise ValueError(
                    f"Invalid JSON at "
                    f"{path}:{line_number}"
                ) from exc

    return records


def sha256_file(path: Path) -> str:
    return hashlib.sha256(
        path.read_bytes()
    ).hexdigest().upper()


def json_block(value: object) -> str:
    return json.dumps(
        value,
        indent=2,
        ensure_ascii=False,
    )


def get_value(
    obj: object,
    field_name: str,
    default: Any = None,
) -> Any:
    value = getattr(
        obj,
        field_name,
        None,
    )

    if value is not None:
        return value

    metadata = getattr(
        obj,
        "metadata",
        None,
    )

    if isinstance(metadata, dict):
        return metadata.get(
            field_name,
            default,
        )

    return default


def extract_chunk_content(
    chunk: object,
) -> str:
    for field_name in (
        "content",
        "text",
        "chunk_text",
    ):
        value = get_value(
            chunk,
            field_name,
        )

        if (
            isinstance(value, str)
            and value.strip()
        ):
            return value.strip()

    return ""


def build_chunk_index() -> dict[str, object]:
    serializer = ChunkSerializer()

    chunks = serializer.load_jsonl(
        CHUNKS_PATH
    )

    index: dict[str, object] = {}

    for chunk in chunks:
        chunk_id = str(
            get_value(
                chunk,
                "chunk_id",
                "",
            )
        ).strip()

        if not chunk_id:
            raise RuntimeError(
                "Canonical corpus contains "
                "a chunk without chunk_id."
            )

        if chunk_id in index:
            raise RuntimeError(
                "Duplicate chunk_id in "
                f"canonical corpus: {chunk_id}"
            )

        index[chunk_id] = chunk

    return index


def enrich_sources(
    sources: list[dict],
    chunk_by_id: dict[str, object],
) -> list[dict]:
    enriched: list[dict] = []

    for source in sources:
        chunk_id = str(
            source["chunk_id"]
        )

        chunk = chunk_by_id.get(
            chunk_id
        )

        if chunk is None:
            raise RuntimeError(
                "Source chunk is missing "
                "from canonical corpus: "
                f"{chunk_id}"
            )

        expected_document_id = str(
            source["document_id"]
        )

        actual_document_id = str(
            get_value(
                chunk,
                "document_id",
                "",
            )
        )

        if (
            actual_document_id
            != expected_document_id
        ):
            raise RuntimeError(
                "Source/document mismatch for "
                f"chunk {chunk_id}: "
                f"expected document_id="
                f"{expected_document_id}, "
                f"actual={actual_document_id}"
            )

        content = extract_chunk_content(
            chunk
        )

        if not content:
            raise RuntimeError(
                "Canonical chunk has no usable "
                f"content: {chunk_id}"
            )

        enriched.append(
            {
                **source,
                "content": content,
            }
        )

    return enriched


def main() -> None:
    cases = load_jsonl(
        CASES_PATH
    )

    results = load_jsonl(
        RESULTS_PATH
    )

    case_by_id = {
        case["case_id"]: case
        for case in cases
    }

    if len(results) != len(cases):
        raise RuntimeError(
            "Case/result count mismatch: "
            f"{len(cases)} cases vs "
            f"{len(results)} results"
        )

    chunk_by_id = build_chunk_index()

    lines: list[str] = [
        "# E2E Human Semantic Review v1",
        "",
        "## Frozen input",
        "",
        f"- Cases: `{CASES_PATH.as_posix()}`",
        f"- Results: `{RESULTS_PATH.as_posix()}`",
        f"- Corpus: `{CHUNKS_PATH.as_posix()}`",
        (
            "- Results SHA256: "
            f"`{sha256_file(RESULTS_PATH)}`"
        ),
        (
            "- Corpus SHA256: "
            f"`{sha256_file(CHUNKS_PATH)}`"
        ),
        "",
        "## Review policy",
        "",
        (
            "Judge only from the query, answer, "
            "and exact retrieved evidence shown below."
        ),
        (
            "Do not silently use external knowledge "
            "to repair unsupported claims."
        ),
        "",
        (
            "The evidence content is reconstructed "
            "from the canonical chunk corpus using "
            "the exact chunk_id returned by the "
            "canonical E2E HTTP run."
        ),
        "",
        "Scores: `2 = pass`, `1 = partial`, "
        "`0 = fail`, `N/A = not applicable`.",
        "",
    ]

    for result in results:
        case_id = result["case_id"]

        if case_id not in case_by_id:
            raise RuntimeError(
                f"Unknown result case: {case_id}"
            )

        case = case_by_id[
            case_id
        ]

        sources = result.get(
            "sources",
            [],
        )

        if not isinstance(
            sources,
            list,
        ):
            raise RuntimeError(
                f"{case_id}: sources is not a list"
            )

        enriched_sources = enrich_sources(
            sources,
            chunk_by_id,
        )

        lines.extend(
            [
                "---",
                "",
                f"# {case_id}",
                "",
                f"**Category:** "
                f"`{case.get('category')}`",
                "",
                f"**Expected behavior:** "
                f"`{case.get('expected_behavior')}`",
                "",
                "## Query",
                "",
                str(case["query"]),
                "",
                "## Model answer",
                "",
                str(result.get("answer", "")),
                "",
                "## API citations",
                "",
                "```json",
                json_block(
                    result.get(
                        "citations",
                        [],
                    )
                ),
                "```",
                "",
                "## Exact retrieved evidence",
                "",
            ]
        )

        for source in enriched_sources:
            citation_id = source[
                "citation_id"
            ]

            lines.extend(
                [
                    (
                        f"### Source "
                        f"[{citation_id}]"
                    ),
                    "",
                    (
                        f"- Source: "
                        f"`{source.get('source')}`"
                    ),
                    (
                        f"- Title: "
                        f"`{source.get('title')}`"
                    ),
                    (
                        f"- Document ID: "
                        f"`{source['document_id']}`"
                    ),
                    (
                        f"- Chunk ID: "
                        f"`{source['chunk_id']}`"
                    ),
                    "",
                    "```text",
                    source["content"],
                    "```",
                    "",
                ]
            )

        lines.extend(
            [
                "## Human scores",
                "",
                "- Correctness: `TODO`",
                "- Faithfulness: `TODO`",
                (
                    "- Citation correctness: "
                    "`TODO`"
                ),
                (
                    "- Citation completeness: "
                    "`TODO`"
                ),
                (
                    "- Evidence sufficiency: "
                    "`TODO`"
                ),
                (
                    "- Ambiguity handling: "
                    "`TODO`"
                ),
                (
                    "- Multi-source synthesis: "
                    "`TODO`"
                ),
                "- Abstention: `TODO`",
                "",
                "**Verdict:** `TODO`",
                "",
                (
                    "**Severity / blocker:** "
                    "`TODO`"
                ),
                "",
                "**Reviewer notes:**",
                "",
                "TODO",
                "",
            ]
        )

    OUTPUT_PATH.parent.mkdir(
        parents=True,
        exist_ok=True,
    )

    OUTPUT_PATH.write_text(
        "\n".join(lines) + "\n",
        encoding="utf-8",
    )

    print("=" * 72)
    print(
        "E2E HUMAN REVIEW PACKET V1"
    )
    print("=" * 72)
    print(
        f"Cases          : {len(cases)}"
    )
    print(
        f"Results        : {len(results)}"
    )
    print(
        f"Corpus chunks  : "
        f"{len(chunk_by_id)}"
    )
    print(
        "Results SHA256 : "
        f"{sha256_file(RESULTS_PATH)}"
    )
    print(
        "Corpus SHA256  : "
        f"{sha256_file(CHUNKS_PATH)}"
    )
    print(
        f"Output         : {OUTPUT_PATH}"
    )


if __name__ == "__main__":
    main()
