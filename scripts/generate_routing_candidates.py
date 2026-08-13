from __future__ import annotations

import argparse
import json
from dataclasses import asdict, dataclass
from pathlib import Path
from typing import Any

from generate_benchmark_candidates import (
    build_retrievers,
    fuse_candidates,
    write_candidates_jsonl,
)


PROJECT_ROOT = Path(__file__).resolve().parents[1]

DEFAULT_CASES_PATH = (
    PROJECT_ROOT
    / "benchmarks"
    / "retrieval"
    / "routing"
    / "development_cases.jsonl"
)

DEFAULT_CHUNKS_PATH = (
    PROJECT_ROOT
    / "data"
    / "processed"
    / "chunks_fixed.jsonl"
)

DEFAULT_OUTPUT_PATH = (
    PROJECT_ROOT
    / "benchmarks"
    / "retrieval"
    / "routing"
    / "candidates.jsonl"
)

DEFAULT_REVIEW_DIR = (
    PROJECT_ROOT
    / "benchmarks"
    / "retrieval"
    / "routing"
    / "review"
)


@dataclass(frozen=True)
class RoutingCase:
    case_id: str
    query: str
    initial_label: str
    reason: str
    status: str


def load_routing_cases(
    path: Path,
) -> list[RoutingCase]:
    cases: list[RoutingCase] = []

    with path.open("r", encoding="utf-8") as file:
        for line_number, line in enumerate(
            file,
            start=1,
        ):
            line = line.strip()

            if not line:
                continue

            record = json.loads(line)

            try:
                case = RoutingCase(
                    case_id=record["case_id"],
                    query=record["query"],
                    initial_label=record["initial_label"],
                    reason=record["reason"],
                    status=record["status"],
                )
            except KeyError as exc:
                raise ValueError(
                    f"Missing field {exc!s} "
                    f"at line {line_number}"
                ) from exc

            cases.append(case)

    return cases


def generate_candidates(
    cases: list[RoutingCase],
    dense_retriever: Any,
    bm25_retriever: Any,
    *,
    retrieval_top_k: int,
    candidate_documents: int,
) -> list[dict[str, Any]]:
    records: list[dict[str, Any]] = []

    total = len(cases)

    for index, case in enumerate(
        cases,
        start=1,
    ):
        print(
            f"[{index:03d}/{total:03d}] "
            f"{case.case_id}"
        )

        dense_results = dense_retriever.retrieve(
            case.query,
            top_k=retrieval_top_k,
            max_chunks_per_document=None,
            candidate_multiplier=5,
        )

        bm25_results = bm25_retriever.retrieve(
            case.query,
            top_k=retrieval_top_k,
            max_chunks_per_document=None,
            candidate_multiplier=5,
        )

        candidates = fuse_candidates(
            dense_results,
            bm25_results,
            top_documents=candidate_documents,
        )

        records.append(
            {
                "case_id": case.case_id,
                "query": case.query,

                # Compatibility with the existing
                # review markdown writer.
                "category": case.initial_label,
                "source_hint": None,
                "state": case.status,

                # Preserve routing-specific metadata.
                "initial_label": case.initial_label,
                "reason": case.reason,
                "candidates": [
                    asdict(candidate)
                    for candidate in candidates
                ],
            }
        )

    return records

def write_routing_review_markdown(
    records: list[dict[str, Any]],
    review_dir: Path,
) -> None:
    review_dir.mkdir(
        parents=True,
        exist_ok=True,
    )

    grouped: dict[str, list[dict[str, Any]]] = {}

    for record in records:
        label = record["initial_label"]

        grouped.setdefault(
            label,
            [],
        ).append(record)

    for label, label_records in grouped.items():
        output_path = (
            review_dir
            / f"{label}_candidates.md"
        )

        with output_path.open(
            "w",
            encoding="utf-8",
            newline="\n",
        ) as file:
            title = label.replace(
                "_",
                " ",
            ).title()

            file.write(
                f"# {title} Ground-Truth Candidates\n\n"
            )

            file.write(
                "> These documents are retrieval "
                "candidates only. Assign relevance "
                "manually before promotion.\n\n"
            )

            file.write(
                "Relevance scale:\n\n"
            )

            file.write(
                "- `3` = highly relevant\n"
                "- `2` = relevant\n"
                "- `1` = marginally relevant\n"
                "- `0` = not relevant\n\n"
            )

            for record in label_records:
                file.write(
                    f"## {record['case_id']}\n\n"
                )

                file.write(
                    f"**Query:** {record['query']}\n\n"
                )

                file.write(
                    "**Initial routing hypothesis:** "
                    f"`{record['initial_label']}`\n\n"
                )

                file.write(
                    f"**Reason:** {record['reason']}\n\n"
                )

                for index, candidate in enumerate(
                    record["candidates"],
                    start=1,
                ):
                    file.write(
                        f"### Candidate {index}\n\n"
                    )

                    file.write(
                        f"- Source: "
                        f"`{candidate['source']}`\n"
                    )

                    file.write(
                        f"- Path: "
                        f"`{candidate['path']}`\n"
                    )

                    title = candidate.get("title")

                    if title:
                        file.write(
                            f"- Title: {title}\n"
                        )

                    file.write(
                        f"- Dense rank: "
                        f"{candidate['dense_rank']}\n"
                    )

                    file.write(
                        f"- BM25 rank: "
                        f"{candidate['bm25_rank']}\n"
                    )

                    file.write(
                        f"- RRF score: "
                        f"{candidate['rrf_score']:.8f}\n\n"
                    )

                    file.write(
                        "**Excerpt:**\n\n"
                    )

                    file.write(
                        f"{candidate['excerpt']}\n\n"
                    )

                    file.write(
                        "**Relevance:** [ ]\n\n"
                    )

                    file.write(
                        "**Notes:**\n\n"
                    )

                    file.write("---\n\n")

def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description=(
            "Generate retrieval candidates for "
            "Adaptive Retrieval routing "
            "ground-truth review."
        )
    )
    
    parser.add_argument(
        "--case-id",
        action="append",
        default=None,
        help=(
            "Process only the specified routing case. "
            "Repeat this option to select multiple cases."
        ),
    )

    parser.add_argument(
        "--cases",
        type=Path,
        default=DEFAULT_CASES_PATH,
    )

    parser.add_argument(
        "--chunks",
        type=Path,
        default=DEFAULT_CHUNKS_PATH,
    )

    parser.add_argument(
        "--output",
        type=Path,
        default=DEFAULT_OUTPUT_PATH,
    )

    parser.add_argument(
        "--review-dir",
        type=Path,
        default=DEFAULT_REVIEW_DIR,
    )

    parser.add_argument(
        "--retrieval-top-k",
        type=int,
        default=30,
    )

    parser.add_argument(
        "--candidate-docs",
        type=int,
        default=10,
    )

    return parser.parse_args()


def main() -> None:
    args = parse_args()

    print("=" * 72)
    print("ROUTING GROUND-TRUTH CANDIDATE GENERATOR")
    print("=" * 72)

    cases = load_routing_cases(args.cases)

    active_cases = [
        case
        for case in cases
        if case.status == "active"
    ]
    
    if args.case_id:
        requested_case_ids = set(args.case_id)

        active_cases = [
            case
            for case in active_cases
            if case.case_id in requested_case_ids
        ]

        found_case_ids = {
            case.case_id
            for case in active_cases
        }

        missing_case_ids = (
            requested_case_ids
            - found_case_ids
        )

        if missing_case_ids:
            missing = ", ".join(
                sorted(missing_case_ids)
            )

            raise ValueError(
                "Unknown or inactive routing case IDs: "
                f"{missing}"
            )

    print(f"Cases loaded : {len(cases)}")
    print(f"Active cases : {len(active_cases)}")

    if not active_cases:
        print("No active routing cases found.")
        return

    dense_retriever, bm25_retriever = (
        build_retrievers(args.chunks)
    )

    records = generate_candidates(
        cases=active_cases,
        dense_retriever=dense_retriever,
        bm25_retriever=bm25_retriever,
        retrieval_top_k=args.retrieval_top_k,
        candidate_documents=args.candidate_docs,
    )

    write_candidates_jsonl(
        records,
        args.output,
    )

    write_routing_review_markdown(
        records,
        args.review_dir,
    )

    print()
    print("=" * 72)
    print("DONE")
    print("=" * 72)
    print(f"Candidate JSONL : {args.output}")
    print(f"Review directory: {args.review_dir}")
    print(f"Cases processed : {len(records)}")


if __name__ == "__main__":
    main()