from __future__ import annotations

import json

from pathlib import Path

from backend.chunking.serializer import ChunkSerializer
from backend.embedding.embedder import LocalEmbedder
from backend.retrieval.bm25_retriever import BM25Retriever
from backend.retrieval.dense_retriever import DenseRetriever
from backend.retrieval.hybrid_retriever import HybridRetriever
from backend.vector_store.qdrant_store import QdrantVectorStore


PROJECT_ROOT = Path(__file__).resolve().parents[1]

CASES_PATH = (
    PROJECT_ROOT
    / "benchmarks"
    / "retrieval"
    / "cases.jsonl"
)

CHUNKS_PATH = (
    PROJECT_ROOT
    / "data"
    / "processed"
    / "chunks_fixed.jsonl"
)

OUTPUT_DIR = (
    PROJECT_ROOT
    / "benchmarks"
    / "retrieval"
    / "ci"
)

OUTPUT_CASES_PATH = (
    OUTPUT_DIR
    / "cases.jsonl"
)

OUTPUT_CHUNKS_PATH = (
    OUTPUT_DIR
    / "chunks.jsonl"
)

COLLECTION_NAME = (
    "enterprise_knowledge_fixed_bge_small"
)

SELECTED_CASE_IDS = {
    # lexical
    "docker_entrypoint_001",
    "kubernetes_configmap_lexical_001",
    "fastapi_depends_001",
    "langgraph_interrupt_lexical_001",
    "qdrant_hnsw_001",

    # semantic
    "docker_multistage_semantic_001",
    "kubernetes_resource_limits_semantic_001",
    "langgraph_branching_semantic_001",
    "qdrant_similarity_semantic_001",
    "huggingface_tokenization_semantic_001",

    # ambiguous
    "docker_small_image_ambiguous_001",
    "kubernetes_health_ambiguous_001",
    "fastapi_cross_cutting_ambiguous_001",
    "langgraph_human_ambiguous_001",
    "qdrant_keyword_semantic_ambiguous_001",

    # version-specific
    "fastapi_pydantic_v1_v2_001",
    "kubernetes_ingress_version_001",
    "kubernetes_version_skew_001",
    "docker_builder_version_001",
    "langgraph_api_migration_001",

    # cross-tool
    "fastapi_kubernetes_001",
    "fastapi_huggingface_001",
    "langgraph_fastapi_qdrant_001",
    "docker_kubernetes_config_001",
    "rag_stack_001",
}

MINING_TOP_K = 30
MAX_NEGATIVES_PER_CASE = 20


def load_selected_cases() -> list[dict]:
    selected_cases = []

    with CASES_PATH.open(
        "r",
        encoding="utf-8",
    ) as file:
        for line in file:
            line = line.strip()

            if not line:
                continue

            record = json.loads(line)

            if (
                record["case_id"]
                not in SELECTED_CASE_IDS
            ):
                continue

            selected_cases.append(
                record
            )

    found_case_ids = {
        case["case_id"]
        for case in selected_cases
    }

    missing_case_ids = (
        SELECTED_CASE_IDS
        - found_case_ids
    )

    if missing_case_ids:
        raise ValueError(
            "Missing selected cases: "
            + ", ".join(
                sorted(missing_case_ids)
            )
        )

    return selected_cases


def collect_ground_truth_documents(
    cases: list[dict],
) -> set[tuple[str, str]]:
    documents: set[
        tuple[str, str]
    ] = set()

    for case in cases:
        for document in (
            case["relevant_documents"]
        ):
            documents.add(
                (
                    document["source"],
                    document["path"],
                )
            )

    return documents


def build_retriever(
    chunks,
) -> HybridRetriever:
    embedder = LocalEmbedder(
        model_name="BAAI/bge-small-en-v1.5",
    )

    vector_store = QdrantVectorStore(
        collection_name=COLLECTION_NAME,
        vector_size=embedder.dimension,
    )

    dense = DenseRetriever(
        embedder=embedder,
        vector_store=vector_store,
    )

    bm25 = BM25Retriever(
        chunks=chunks,
    )

    return HybridRetriever(
        dense_retriever=dense,
        bm25_retriever=bm25,
        rrf_k=60,
        dense_weight=0.7,
        bm25_weight=0.3,
    )


def main() -> None:
    OUTPUT_DIR.mkdir(
        parents=True,
        exist_ok=True,
    )

    selected_cases = (
        load_selected_cases()
    )

    ground_truth_documents = (
        collect_ground_truth_documents(
            selected_cases
        )
    )

    serializer = ChunkSerializer()

    chunks = serializer.load_jsonl(
        CHUNKS_PATH
    )

    chunks_by_id = {
        chunk.chunk_id: chunk
        for chunk in chunks
    }

    ground_truth_chunks = {
        chunk.chunk_id: chunk
        for chunk in chunks
        if (
            chunk.source,
            chunk.relative_path,
        )
        in ground_truth_documents
    }

    retriever = build_retriever(
        chunks
    )

    hard_negative_chunk_ids: set[
        str
    ] = set()

    for case in selected_cases:
        results = retriever.retrieve(
            query=case["query"],
            top_k=MINING_TOP_K,
            max_chunks_per_document=1,
            candidate_multiplier=5,
        )

        selected_for_case = 0

        for result in results:
            document_key = (
                result.source,
                result.relative_path,
            )

            if (
                document_key
                in ground_truth_documents
            ):
                continue

            hard_negative_chunk_ids.add(
                result.chunk_id
            )

            selected_for_case += 1

            if (
                selected_for_case
                >= MAX_NEGATIVES_PER_CASE
            ):
                break

    hard_negative_chunks = {
        chunk_id: chunks_by_id[chunk_id]
        for chunk_id in hard_negative_chunk_ids
        if chunk_id in chunks_by_id
    }

    ci_chunks = {
        **ground_truth_chunks,
        **hard_negative_chunks,
    }

    with OUTPUT_CASES_PATH.open(
        "w",
        encoding="utf-8",
    ) as file:
        for case in selected_cases:
            file.write(
                json.dumps(
                    case,
                    ensure_ascii=False,
                )
                + "\n"
            )

    with OUTPUT_CHUNKS_PATH.open(
        "w",
        encoding="utf-8",
    ) as file:
        for chunk_id in sorted(
            ci_chunks
        ):
            chunk = ci_chunks[
                chunk_id
            ]

            record = {
                "chunk_id": chunk.chunk_id,
                "document_id": (
                    chunk.document_id
                ),
                "content": chunk.content,
                "chunk_index": (
                    chunk.chunk_index
                ),
                "token_count": (
                    chunk.token_count
                ),
                "source": chunk.source,
                "filename": chunk.filename,
                "relative_path": (
                    chunk.relative_path
                ),
                "title": chunk.title,
            }

            file.write(
                json.dumps(
                    record,
                    ensure_ascii=False,
                )
                + "\n"
            )

    print()
    print("=" * 80)
    print(
        "CI RETRIEVAL CORPUS GENERATED"
    )
    print("=" * 80)

    print(
        f"Cases: "
        f"{len(selected_cases)}"
    )

    print(
        f"Ground-truth documents: "
        f"{len(ground_truth_documents)}"
    )

    print(
        f"Ground-truth chunks: "
        f"{len(ground_truth_chunks)}"
    )

    print(
        f"Hard-negative chunks: "
        f"{len(hard_negative_chunks)}"
    )

    print(
        f"Total CI chunks: "
        f"{len(ci_chunks)}"
    )

    print()
    print(
        f"Cases written to: "
        f"{OUTPUT_CASES_PATH}"
    )

    print(
        f"Chunks written to: "
        f"{OUTPUT_CHUNKS_PATH}"
    )


if __name__ == "__main__":
    main()