from __future__ import annotations

import os
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
from backend.retrieval.hybrid_retriever import (
    HybridRetriever,
)
from backend.retrieval.models import RetrievalResult
from backend.retrieval.rank_bm25_query_encoder import (
    RankBM25QueryEncoder,
)


PROJECT_ROOT = Path(__file__).resolve().parents[1]

DATASET_PATH = (
    PROJECT_ROOT
    / "benchmarks"
    / "retrieval"
    / "cases.jsonl"
)

ARTIFACT_PATH = (
    PROJECT_ROOT
    / ".benchmark-results"
    / "rank-bm25-query-artifact-v1.json"
)

COLLECTION_NAME = (
    "enterprise_knowledge_cloud_bge_rank_bm25_v1"
)

BGE_MODEL = "BAAI/bge-small-en-v1.5"

DENSE_VECTOR = "dense_vector"
SPARSE_VECTOR = "rank_bm25_sparse"

TOP_K = 10
RRF_K = 60
DENSE_WEIGHT = 0.7
BM25_WEIGHT = 0.3


class FastEmbedCloudDenseRetriever:
    def __init__(
        self,
        *,
        model: TextEmbedding,
        client: QdrantClient,
        collection_name: str,
        vector_name: str,
    ) -> None:
        self.model = model
        self.client = client
        self.collection_name = collection_name
        self.vector_name = vector_name

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
            using=self.vector_name,
            limit=search_limit,
            with_payload=True,
        )

        results: list[RetrievalResult] = []
        document_counts: dict[str, int] = defaultdict(int)

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
                        payload.get("chunk_id", "")
                    ),
                    document_id=document_id,
                    content=str(
                        payload.get("content", "")
                    ),
                    score=float(point.score),
                    rank=len(results) + 1,
                    source=str(
                        payload.get("source", "")
                    ),
                    filename=str(
                        payload.get("filename", "")
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


class ExactBM25CloudRetriever:
    def __init__(
        self,
        *,
        encoder: RankBM25QueryEncoder,
        client: QdrantClient,
        collection_name: str,
        vector_name: str,
    ) -> None:
        self.encoder = encoder
        self.client = client
        self.collection_name = collection_name
        self.vector_name = vector_name

    def retrieve(
        self,
        query: str,
        top_k: int = 5,
        max_chunks_per_document: int | None = None,
        candidate_multiplier: int = 5,
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

        query_vector = self.encoder.encode(
            query
        )

        if query_vector is None:
            return []

        search_limit = top_k

        if max_chunks_per_document is not None:
            search_limit = (
                top_k * candidate_multiplier
            )

        response = self.client.query_points(
            collection_name=self.collection_name,
            query=query_vector,
            using=self.vector_name,
            limit=search_limit,
            with_payload=True,
        )

        results: list[RetrievalResult] = []
        document_counts: dict[str, int] = defaultdict(int)

        for point in response.points:
            score = float(point.score)

            if score <= 0:
                continue

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
                        payload.get("chunk_id", "")
                    ),
                    document_id=document_id,
                    content=str(
                        payload.get("content", "")
                    ),
                    score=score,
                    rank=len(results) + 1,
                    source=str(
                        payload.get("source", "")
                    ),
                    filename=str(
                        payload.get("filename", "")
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


def _require_env(name: str) -> str:
    value = os.getenv(name, "").strip()

    if not value:
        raise RuntimeError(
            f"{name} is required. "
            "Set it in the current shell "
            "before running."
        )

    return value


def main() -> None:
    qdrant_url = _require_env(
        "QDRANT_URL"
    )

    qdrant_api_key = _require_env(
        "QDRANT_API_KEY"
    )

    if not ARTIFACT_PATH.exists():
        raise FileNotFoundError(
            "rank_bm25 query artifact "
            f"not found: {ARTIFACT_PATH}"
        )

    cases = load_evaluation_cases(
        DATASET_PATH
    )

    if not cases:
        raise ValueError(
            "No active evaluation cases found."
        )

    encoder = RankBM25QueryEncoder(
        ARTIFACT_PATH
    )

    artifact_size_mb = (
        ARTIFACT_PATH.stat().st_size
        / (1024 * 1024)
    )

    print(
        "FINAL EXACT CLOUD RETRIEVAL CANDIDATE"
    )
    print(
        "====================================="
    )
    print(
        f"Cases: {len(cases)}"
    )
    print(
        f"Collection: {COLLECTION_NAME}"
    )
    print(
        f"Dense query model: {BGE_MODEL} "
        "(FastEmbed)"
    )
    print(
        "Dense document vectors: "
        "canonical BGE vectors"
    )
    print(
        "Sparse query encoder: "
        "exact rank_bm25 artifact"
    )
    print(
        f"Sparse vector: {SPARSE_VECTOR}"
    )
    print(
        f"Artifact terms: "
        f"{len(encoder.term_table):,}"
    )
    print(
        f"Artifact size: "
        f"{artifact_size_mb:.2f} MB"
    )
    print(
        f"Artifact corpus chunks: "
        f"{encoder.corpus_chunks:,}"
    )
    print(
        f"Weighted RRF: "
        f"dense={DENSE_WEIGHT} "
        f"bm25={BM25_WEIGHT} "
        f"k={RRF_K}"
    )
    print(
        f"Top K: {TOP_K}"
    )
    print()

    client = QdrantClient(
        url=qdrant_url,
        api_key=qdrant_api_key,
        timeout=120.0,
    )

    model = TextEmbedding(
        model_name=BGE_MODEL,
        lazy_load=True,
    )

    dense_retriever = (
        FastEmbedCloudDenseRetriever(
            model=model,
            client=client,
            collection_name=COLLECTION_NAME,
            vector_name=DENSE_VECTOR,
        )
    )

    bm25_retriever = (
        ExactBM25CloudRetriever(
            encoder=encoder,
            client=client,
            collection_name=COLLECTION_NAME,
            vector_name=SPARSE_VECTOR,
        )
    )

    retriever = HybridRetriever(
        dense_retriever=dense_retriever,
        bm25_retriever=bm25_retriever,
        rrf_k=RRF_K,
        dense_weight=DENSE_WEIGHT,
        bm25_weight=BM25_WEIGHT,
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
        case_started_at = time.perf_counter()

        result = evaluator.evaluate_case(
            case=case,
            top_k=TOP_K,
        )

        results.append(result)

        latency_ms = (
            time.perf_counter()
            - case_started_at
        ) * 1000

        first_rank = (
            result.first_relevant_rank
            if result.first_relevant_rank
            is not None
            else "-"
        )

        print(
            f"[{index:03d}/{len(cases):03d}] "
            f"{case.case_id} "
            f"first_relevant_rank="
            f"{first_rank} "
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
        "FASTEMBED BGE + EXACT RANK_BM25 CLOUD",
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

    mean_case_latency_ms = (
        total_seconds
        / len(cases)
        * 1000
    )

    print()
    print(
        "BENCHMARK RUNTIME"
    )
    print(
        "================="
    )
    print(
        f"Total seconds: "
        f"{total_seconds:.2f}"
    )
    print(
        "Mean case latency ms: "
        f"{mean_case_latency_ms:.2f}"
    )

    print()
    print(
        "CANONICAL LOCAL WEIGHTED RRF "
        "REFERENCE"
    )
    print(
        "================================"
    )
    print(
        "Hit@1      0.6200"
    )
    print(
        "Hit@3      0.8100"
    )
    print(
        "Hit@5      0.8700"
    )
    print(
        "Hit@10     0.9300"
    )
    print(
        "Recall@3   0.6408"
    )
    print(
        "Recall@5   0.7308"
    )
    print(
        "Recall@10  0.8392"
    )
    print(
        "nDCG@3     0.6010"
    )
    print(
        "nDCG@5     0.6402"
    )
    print(
        "nDCG@10    0.6788"
    )
    print(
        "MRR        0.7247"
    )

    print()
    print(
        "This is the final retrieval quality "
        "gate for the free-tier deployment "
        "architecture."
    )


if __name__ == "__main__":
    main()