from __future__ import annotations

import json
from pathlib import Path

import numpy as np
from sentence_transformers import SentenceTransformer


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

MODEL_NAME = "BAAI/bge-small-en-v1.5"

# Review threshold only.
# A score above this value is NOT automatically leakage.
REVIEW_THRESHOLD = 0.82

TOP_N = 3


def load_jsonl(path: Path) -> list[dict]:
    records = []

    with path.open("r", encoding="utf-8") as file:
        for line in file:
            line = line.strip()

            if line:
                records.append(json.loads(line))

    return records


def main() -> None:
    canonical_cases = load_jsonl(CANONICAL_CASES)
    routing_cases = load_jsonl(ROUTING_CASES)

    print("=" * 80)
    print("ADAPTIVE RETRIEVAL SEMANTIC OVERLAP CHECK")
    print("=" * 80)
    print(f"Canonical cases : {len(canonical_cases)}")
    print(f"Routing cases   : {len(routing_cases)}")
    print(f"Embedding model : {MODEL_NAME}")
    print(f"Review threshold: {REVIEW_THRESHOLD:.2f}")
    print()

    model = SentenceTransformer(MODEL_NAME)

    canonical_queries = [
        case["query"]
        for case in canonical_cases
    ]

    routing_queries = [
        case["query"]
        for case in routing_cases
    ]

    canonical_embeddings = model.encode(
        canonical_queries,
        normalize_embeddings=True,
        show_progress_bar=True,
    )

    routing_embeddings = model.encode(
        routing_queries,
        normalize_embeddings=True,
        show_progress_bar=True,
    )

    # Embeddings are normalized, so dot product = cosine similarity.
    similarities = (
        routing_embeddings
        @ canonical_embeddings.T
    )

    flagged_pairs = []

    for routing_index, routing_case in enumerate(
        routing_cases
    ):
        scores = similarities[routing_index]

        top_indices = np.argsort(scores)[::-1][:TOP_N]

        for canonical_index in top_indices:
            score = float(scores[canonical_index])

            if score < REVIEW_THRESHOLD:
                continue

            canonical_case = canonical_cases[
                canonical_index
            ]

            flagged_pairs.append(
                (
                    score,
                    routing_case,
                    canonical_case,
                )
            )

    flagged_pairs.sort(
        key=lambda item: item[0],
        reverse=True,
    )

    print("FLAGGED SEMANTIC NEIGHBORS")
    print("-" * 80)

    if not flagged_pairs:
        print(
            "No pairs exceeded the review threshold."
        )
    else:
        for (
            score,
            routing_case,
            canonical_case,
        ) in flagged_pairs:
            print(f"Similarity : {score:.4f}")

            print(
                "Routing    : "
                f'{routing_case["case_id"]}'
            )
            print(
                f'  {routing_case["query"]}'
            )

            print(
                "Canonical  : "
                f'{canonical_case["case_id"]}'
            )
            print(
                f'  {canonical_case["query"]}'
            )

            print()

    print("=" * 80)
    print("SUMMARY")
    print("=" * 80)
    print(
        f"Flagged pairs >= {REVIEW_THRESHOLD:.2f}: "
        f"{len(flagged_pairs)}"
    )


if __name__ == "__main__":
    main()