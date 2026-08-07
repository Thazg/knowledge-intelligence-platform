import json
from pathlib import Path

from backend.chunking.serializer import ChunkSerializer
from backend.embedding.embedder import LocalEmbedder
from backend.evaluation.retrieval_evaluator import (
    EvaluationCase,
    RetrievalEvaluator,
)
from backend.query_rewriting.query_rewriter import QueryRewriter
from backend.retrieval.bm25_retriever import BM25Retriever
from backend.retrieval.dense_retriever import DenseRetriever
from backend.retrieval.hybrid_retriever import HybridRetriever
from backend.retrieval.multi_query_retriever import MultiQueryRetriever
from backend.vector_store.qdrant_store import QdrantVectorStore
from backend.query_rewriting.frozen_query_rewriter import (
    FrozenQueryRewriter,
)

PROJECT_ROOT = Path(__file__).resolve().parents[1]
DATASET_PATH = Path(
    "backend/evaluation/datasets/retrieval_cases.jsonl"
)
CHUNKS_PATH = (
    PROJECT_ROOT
    / "data"
    / "processed"
    / "chunks_fixed.jsonl"
)
COLLECTION_NAME = "enterprise_knowledge_fixed_bge_small"


def load_cases(
    path: Path,
) -> list[EvaluationCase]:

    cases: list[EvaluationCase] = []

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

            record = json.loads(line)

            if record.get("status") != "active":
                continue

            cases.append(
                EvaluationCase(
                    case_id=record["id"],
                    query=record["query"],
                    expected_source=record[
                        "expected_source"
                    ],
                    expected_path=record[
                        "expected_path"
                    ],
                )
            )

    return cases


def mean(values: list[float]) -> float:
    if not values:
        return 0.0

    return sum(values) / len(values)

def normalize_path(path: str) -> str:
    return path.replace("\\", "/").lower()


def find_relevant_rank(
    results,
    expected_source: str,
    expected_path: str,
) -> int | None:
    expected_source = expected_source.lower()
    expected_path = normalize_path(expected_path)

    for result in results:
        result_source = result.source.lower()
        result_path = normalize_path(
            result.relative_path
        )

        if (
            result_source == expected_source
            and result_path == expected_path
        ):
            return result.rank

    return None

def main() -> None:

    cases = load_cases(DATASET_PATH)

    if not cases:
        raise ValueError(
            "No active evaluation cases found."
        )

    serializer = ChunkSerializer()

    chunks = serializer.load_jsonl(
        CHUNKS_PATH
    )

    print(f"Loaded chunks: {len(chunks):,}")

    embedder = LocalEmbedder(
        model_name="BAAI/bge-small-en-v1.5",
    )

    vector_store = QdrantVectorStore(
        collection_name=COLLECTION_NAME,
        vector_size=embedder.dimension,
    )

    dense_retriever = DenseRetriever(
        embedder=embedder,
        vector_store=vector_store,
    )

    bm25_retriever = BM25Retriever(
        chunks=chunks,
    )
    
    rewrites_path = (
        PROJECT_ROOT
        / "backend"
        / "evaluation"
        / "datasets"
        / "query_rewrites.jsonl"
    )

    query_rewriter = FrozenQueryRewriter(
        rewrites_path=rewrites_path,
    )
    
    hybrid_retriever = HybridRetriever(
        dense_retriever=dense_retriever,
        bm25_retriever=bm25_retriever,
        rrf_k=60,
        dense_weight=0.7,
        bm25_weight=0.3,
    )

    retriever = MultiQueryRetriever(
        base_retriever=hybrid_retriever,
        query_rewriter=query_rewriter,
        rrf_k=60,
        candidate_multiplier=5,
        query_weights=[
            1.0,  # original
            0.7,  # rewrite 1
            0.7,  # rewrite 2
        ],
    )

    evaluator = RetrievalEvaluator(
        retriever=retriever,
    )

    results = evaluator.evaluate(
        cases=cases,
        top_k=10,
    )

    recall_at_1 = mean([
        float(result.hit_at_k(1))
        for result in results
    ])

    recall_at_3 = mean([
        float(result.hit_at_k(3))
        for result in results
    ])

    recall_at_5 = mean([
        float(result.hit_at_k(5))
        for result in results
    ])

    recall_at_10 = mean([
        float(result.hit_at_k(10))
        for result in results
    ])

    mrr = mean([
        result.reciprocal_rank
        for result in results
    ])

    print("=" * 80)
    print("MULTI-QUERY RETRIEVAL EVALUATION")
    print("=" * 80)
    print(f"Cases     : {len(results)}")
    print(f"Hit@1  : {recall_at_1:.4f}")
    print(f"Hit@3  : {recall_at_3:.4f}")
    print(f"Hit@5  : {recall_at_5:.4f}")
    print(f"Hit@10 : {recall_at_10:.4f}")
    print(f"MRR       : {mrr:.4f}")

    print()
    print("=" * 80)
    print("CASE RESULTS")
    print("=" * 80)

    print()
    print("=" * 80)
    print("RANK MOVEMENT ANALYSIS")
    print("=" * 80)

    improved = 0
    unchanged = 0
    degraded = 0

    result_by_case_id = {
        result.case_id: result
        for result in results
    }

    for case in cases:
        hybrid_results = hybrid_retriever.retrieve(
            query=case.query,
            top_k=10,
            max_chunks_per_document=1,
            candidate_multiplier=5,
        )

        hybrid_rank = find_relevant_rank(
            results=hybrid_results,
            expected_source=case.expected_source,
            expected_path=case.expected_path,
        )

        evaluation_result = result_by_case_id[
            case.case_id
        ]

        multi_query_rank = (
            evaluation_result.first_relevant_rank
        )

        print()
        print("-" * 80)
        print(
            f"Case               : "
            f"{case.case_id}"
        )
        print(
            f"Weighted RRF rank  : "
            f"{hybrid_rank or 'MISS'}"
        )
        print(
            f"Multi-Query rank   : "
            f"{multi_query_rank or 'MISS'}"
        )

        if (
            hybrid_rank is None
            and multi_query_rank is not None
        ):
            print(
                "Movement           : IMPROVED"
            )
            improved += 1

        elif (
            hybrid_rank is not None
            and multi_query_rank is None
        ):
            print(
                "Movement           : DEGRADED"
            )
            degraded += 1

        elif (
            hybrid_rank is None
            and multi_query_rank is None
        ):
            print(
                "Movement           : UNCHANGED"
            )
            unchanged += 1

        else:
            delta = (
                hybrid_rank
                - multi_query_rank
            )

            if delta > 0:
                print(
                    "Movement           : "
                    f"IMPROVED (+{delta})"
                )
                improved += 1

            elif delta < 0:
                print(
                    "Movement           : "
                    f"DEGRADED ({delta})"
                )
                degraded += 1

            else:
                print(
                    "Movement           : "
                    "UNCHANGED"
                )
                unchanged += 1

    print()
    print("=" * 80)
    print("RANK MOVEMENT SUMMARY")
    print("=" * 80)
    print(f"Improved : {improved}")
    print(f"Unchanged: {unchanged}")
    print(f"Degraded : {degraded}")


if __name__ == "__main__":
    main()