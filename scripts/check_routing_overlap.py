from __future__ import annotations

import json
import re
from difflib import SequenceMatcher
from pathlib import Path


PROJECT_ROOT = Path(__file__).resolve().parents[1]

CANONICAL_CASES = (
    PROJECT_ROOT
    / "benchmarks"
    / "retrieval"
    / "cases.jsonl"
)

ROUTING_CASES = (
    PROJECT_ROOT
    / "benchmarks"
    / "retrieval"
    / "routing"
    / "development_cases.jsonl"
)

SIMILARITY_THRESHOLD = 0.75


def load_jsonl(path: Path) -> list[dict]:
    records = []

    with path.open("r", encoding="utf-8") as file:
        for line in file:
            line = line.strip()

            if line:
                records.append(json.loads(line))

    return records


def normalize_query(query: str) -> str:
    query = query.lower()
    query = re.sub(r"[^a-z0-9\s]", " ", query)
    query = re.sub(r"\s+", " ", query)

    return query.strip()


def similarity(left: str, right: str) -> float:
    return SequenceMatcher(
        None,
        normalize_query(left),
        normalize_query(right),
    ).ratio()


def main() -> None:
    canonical_cases = load_jsonl(CANONICAL_CASES)
    routing_cases = load_jsonl(ROUTING_CASES)

    print("=" * 80)
    print("ADAPTIVE RETRIEVAL ROUTING OVERLAP CHECK")
    print("=" * 80)
    print(f"Canonical cases : {len(canonical_cases)}")
    print(f"Routing cases   : {len(routing_cases)}")
    print()

    exact_matches = []
    near_matches = []

    canonical_normalized = {
        normalize_query(case["query"]): case
        for case in canonical_cases
    }

    for routing_case in routing_cases:
        routing_query = routing_case["query"]
        normalized = normalize_query(routing_query)

        exact = canonical_normalized.get(normalized)

        if exact is not None:
            exact_matches.append(
                (
                    routing_case,
                    exact,
                )
            )
            continue

        for canonical_case in canonical_cases:
            score = similarity(
                routing_query,
                canonical_case["query"],
            )

            if score >= SIMILARITY_THRESHOLD:
                near_matches.append(
                    (
                        score,
                        routing_case,
                        canonical_case,
                    )
                )

    near_matches.sort(
        key=lambda item: item[0],
        reverse=True,
    )

    print("EXACT MATCHES")
    print("-" * 80)

    if not exact_matches:
        print("None")
    else:
        for routing_case, canonical_case in exact_matches:
            print(
                f'{routing_case["case_id"]} '
                f'<-> {canonical_case["case_id"]}'
            )
            print(f'Routing   : {routing_case["query"]}')
            print(f'Canonical : {canonical_case["query"]}')
            print()

    print()
    print("NEAR MATCHES")
    print("-" * 80)

    if not near_matches:
        print(
            f"No pairs >= {SIMILARITY_THRESHOLD:.2f}"
        )
    else:
        for score, routing_case, canonical_case in near_matches:
            print(f"Similarity: {score:.3f}")
            print(
                f'Routing    : {routing_case["case_id"]}'
            )
            print(f'  {routing_case["query"]}')
            print(
                f'Canonical  : {canonical_case["case_id"]}'
            )
            print(f'  {canonical_case["query"]}')
            print()

    print("=" * 80)
    print("SUMMARY")
    print("=" * 80)
    print(f"Exact matches : {len(exact_matches)}")
    print(f"Near matches  : {len(near_matches)}")


if __name__ == "__main__":
    main()