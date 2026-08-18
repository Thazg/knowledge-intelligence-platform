from __future__ import annotations

import argparse
import time
from collections import defaultdict
from pathlib import Path

from fastembed import TextEmbedding
from qdrant_client import QdrantClient

from backend.evaluation.dataset_loader import (
    load_evaluation_cases,
)
from backend.evaluation.metrics import (
    calculate_metrics,
    calculate_metrics_by_category,
    print_metrics,
)
from backend.evaluation.retrieval_evaluator import (
    RetrievalEvaluator,
)
from backend.retrieval.models import RetrievalResult


PROJECT_ROOT = Path(__file__).resolve().parents[1]

DATASET_PATH = (
    PROJECT_ROOT
    / "benchmarks"
    / "retrieval"
    / "cases.jsonl"
)

DEFAULT_QDRANT_URL = "http://localhost:6333"

COLLECTION_NAME = (
    "enterprise_knowledge_fixed_bge_small"
)

MODEL_NAME = "BAAI/bge-small-en-v1.5"

TOP_K = 10


class FastEmbedBgeRetriever:
    def __init__(
        self,
        *,
        model: TextEmbedding,
        client: QdrantClient,
        collection_name: str,
    ) -> None:
        self.model = model
        self.client = client
        self.collection_name = collection_name

    def retrieve(
        self,
        query: str,
        top_k: int = 5,
        max_chunks_per_document: int | None = None,
        candidate_multiplier: int = 3,
    ) -> list[RetrievalResult]:
        if not query.strip():
            raise ValueError(
                "query must not be empty."
            )

        if top_k <= 0:
            raise ValueError(
                "top_k must be greater than 0."
            )

        if (
            max_chunks_per_document is not None
            and max_chunks_per_document <= 0
        ):
            raise ValueError(
                "max_chunks_per_document "
                "must be greater than 0."
            )

        if candidate_multiplier <= 0:
            raise ValueError(
                "candidate_multiplier "
                "must be greater than 0."
            )

        query_vector = next(
            self.model.query_embed(
                [query]
            )
        ).tolist()

        search_limit = top_k

        if max_chunks_per_document is not None:
            search_limit = (
                top_k * candidate_multiplier
            )

        response = self.client.query_points(
            collection_name=self.collection_name,
            query=query_vector,
            limit=search_limit,
            with_payload=True,
        )

        results: list[RetrievalResult] = []
        document_counts: dict[str, int] = (
            defaultdict(int)
        )

        for point in response.points:
            payload = point.payload or {}

            document_id = str(
                payload.get("document_id", "")
            )

            if max_chunks_per_document is not None:
                if (
                    document_counts[document_id]
                    >= max_chunks_per_document
                ):
                    continue

                document_counts[document_id] += 1

            results.append(
                RetrievalResult(
                    chunk_id=str(
                        payload.get(
                            "chunk_id",
                            "",
                        )
                    ),
                    document_id=document_id,
                    content=str(
                        payload.get(
                            "content",
                            "",
                        )
                    ),
                    score=float(point.score),
                    rank=len(results) + 1,
                    source=str(
                        payload.get(
                            "source",
                            "",
                        )
                    ),
                    filename=str(
                        payload.get(
                            "filename",
                            "",
                        )
                    ),
                    relative_path=str(
                        payload.get(
                            "relative_path",
                            "",
                        )
                    ),
                    chunk_index=int(
                        payload.get(
                            "chunk_index",
                            0,
                        )
                    ),
                    token_count=int(
                        payload.get(
                            "token_count",
                            0,
                        )
                    ),
                    title=payload.get("title"),
                )
            )

            if len(results) >= top_k:
                break

        return results


def _parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description=(
            "Benchmark FastEmbed BGE query "
            "embeddings against the existing "
            "SentenceTransformers BGE Qdrant "
            "collection."
        )
    )

    parser.add_argument(
        "--qdrant-url",
        default=DEFAULT_QDRANT_URL,
    )

    return parser.parse_args()


def main() -> None:
    args = _parse_args()

    cases = load_evaluation_cases(
        DATASET_PATH
    )

    if not cases:
        raise ValueError(
            "No active evaluation cases found."
        )

    print(
        "FASTEMBED BGE COMPATIBILITY BENCHMARK"
    )
    print(
        "====================================="
    )
    print(
        f"Cases: {len(cases)}"
    )
    print(
        f"Model: {MODEL_NAME}"
    )
    print(
        f"Collection: {COLLECTION_NAME}"
    )
    print(
        f"Qdrant URL: {args.qdrant_url}"
    )
    print()

    model = TextEmbedding(
        model_name=MODEL_NAME,
        lazy_load=True,
    )

    client = QdrantClient(
        url=args.qdrant_url,
        timeout=30.0,
    )

    if not client.collection_exists(
        COLLECTION_NAME
    ):
        raise RuntimeError(
            "Local BGE collection does not "
            "exist. Start the local Qdrant "
            "runtime before running this "
            "benchmark."
        )

    retriever = FastEmbedBgeRetriever(
        model=model,
        client=client,
        collection_name=COLLECTION_NAME,
    )

    evaluator = RetrievalEvaluator(
        retriever=retriever,
    )

    results = []

    started_at = time.perf_counter()

    for index, case in enumerate(
        cases,
        start=1,
    ):
        case_started = time.perf_counter()

        result = evaluator.evaluate_case(
            case=case,
            top_k=TOP_K,
        )

        results.append(result)

        latency_ms = (
            time.perf_counter()
            - case_started
        ) * 1000

        first_rank = (
            result.first_relevant_rank
            if result.first_relevant_rank is not None
            else "-"
        )

        print(
            f"[{index:03d}/{len(cases):03d}] "
            f"{case.case_id} "
            f"first_relevant_rank={first_rank} "
            f"latency_ms={latency_ms:.2f}"
        )

    total_seconds = (
        time.perf_counter()
        - started_at
    )

    overall_metrics = calculate_metrics(
        results
    )

    print()
    print_metrics(
        "FASTEMBED BGE → EXISTING BGE VECTORS",
        overall_metrics,
    )

    category_metrics = (
        calculate_metrics_by_category(
            results
        )
    )

    for category in sorted(
        category_metrics
    ):
        print_metrics(
            f"CATEGORY: {category}",
            category_metrics[category],
        )

    print()
    print(
        "RUNTIME"
    )
    print(
        "======="
    )
    print(
        f"Total seconds: {total_seconds:.2f}"
    )
    print(
        "Mean case latency ms: "
        f"{total_seconds / len(cases) * 1000:.2f}"
    )

    print()
    print(
        "LOCAL SENTENCE-TRANSFORMERS "
        "BGE REFERENCE"
    )
    print(
        "================================"
    )
    print(
        "MRR        0.6644"
    )
    print(
        "Recall@10  0.7958"
    )
    print(
        "nDCG@10    0.6364"
    )
    print()
    print(
        "This is a compatibility experiment, "
        "not a new production baseline."
    )


if __name__ == "__main__":
    main()