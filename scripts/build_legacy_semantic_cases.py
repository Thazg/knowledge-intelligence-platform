from __future__ import annotations

import json
from pathlib import Path


PROJECT_ROOT = Path(__file__).resolve().parents[1]

OUTPUT_PATH = (
    PROJECT_ROOT
    / "benchmarks"
    / "retrieval"
    / "legacy_semantic_cases.jsonl"
)


CASES = [
    {
        "case_id": "docker_cache_001",
        "query": "How does Docker build cache work and when is it invalidated?",
        "category": "semantic",
        "status": "active",
        "relevant_documents": [
            {
                "source": "docker",
                "path": "content/get-started/docker-concepts/building-images/using-the-build-cache.md",
                "relevance": 3,
            },
        ],
    },
    {
        "case_id": "kubernetes_configmap_001",
        "query": "How does a Kubernetes ConfigMap provide configuration to a Pod?",
        "category": "semantic",
        "status": "active",
        "relevant_documents": [
            {
                "source": "kubernetes",
                "path": "content/en/docs/tasks/configure-pod-container/configure-pod-configmap.md",
                "relevance": 3,
            },
        ],
    },
    {
        "case_id": "kubernetes_liveness_001",
        "query": "What is the difference between liveness, readiness, and startup probes in Kubernetes?",
        "category": "semantic",
        "status": "active",
        "relevant_documents": [
            {
                "source": "kubernetes",
                "path": "content/en/docs/concepts/workloads/pods/probes.md",
                "relevance": 3,
            },
        ],
    },
    {
        "case_id": "fastapi_background_tasks_001",
        "query": "How do background tasks work in FastAPI?",
        "category": "semantic",
        "status": "active",
        "relevant_documents": [
            {
                "source": "fastapi",
                "path": "en/docs/tutorial/background-tasks.md",
                "relevance": 3,
            },
        ],
    },
    {
        "case_id": "fastapi_middleware_001",
        "query": "How do I add middleware to a FastAPI application?",
        "category": "semantic",
        "status": "active",
        "relevant_documents": [
            {
                "source": "fastapi",
                "path": "en/docs/tutorial/middleware.md",
                "relevance": 3,
            },
        ],
    },
    {
        "case_id": "fastapi_validation_001",
        "query": "How does FastAPI validate request bodies using Pydantic models?",
        "category": "semantic",
        "status": "active",
        "relevant_documents": [
            {
                "source": "fastapi",
                "path": "en/docs/tutorial/body.md",
                "relevance": 3,
            },
        ],
    },
    {
        "case_id": "langgraph_checkpoint_001",
        "query": "How do LangGraph checkpointers persist graph state between executions?",
        "category": "semantic",
        "status": "active",
        "relevant_documents": [
            {
                "source": "langchain",
                "path": "langgraph/checkpointers.mdx",
                "relevance": 3,
            },
        ],
    },
    {
        "case_id": "langgraph_interrupt_001",
        "query": "How can a LangGraph workflow pause for human approval and resume later?",
        "category": "semantic",
        "status": "active",
        "relevant_documents": [
            {
                "source": "langchain",
                "path": "langgraph/interrupts.mdx",
                "relevance": 3,
            },
        ],
    },
    {
        "case_id": "langgraph_state_001",
        "query": "How is shared state defined and updated in a LangGraph graph?",
        "category": "semantic",
        "status": "active",
        "relevant_documents": [
            {
                "source": "langchain",
                "path": "langgraph/graph-api.mdx",
                "relevance": 3,
            },
        ],
    },
    {
        "case_id": "langgraph_memory_001",
        "query": "What is the difference between short-term and long-term memory in LangGraph?",
        "category": "semantic",
        "status": "active",
        "relevant_documents": [
            {
                "source": "langchain",
                "path": "concepts/memory.mdx",
                "relevance": 3,
            },
        ],
    },
    {
        "case_id": "qdrant_filter_001",
        "query": "How do Qdrant payload filters restrict vector search results?",
        "category": "semantic",
        "status": "active",
        "relevant_documents": [
            {
                "source": "qdrant",
                "path": "search/_index.md",
                "relevance": 3,
            },
            {
                "source": "qdrant",
                "path": "manage-data/indexing.md",
                "relevance": 2,
            },
        ],
    },
    {
        "case_id": "qdrant_hybrid_001",
        "query": "How does hybrid search combine dense and sparse vectors in Qdrant?",
        "category": "semantic",
        "status": "active",
        "relevant_documents": [
            {
                "source": "qdrant",
                "path": "search/text-search/hybrid-search.md",
                "relevance": 3,
            },
            {
                "source": "qdrant",
                "path": "tutorials-basics/cloud-inference-hybrid-search.md",
                "relevance": 2,
            },
            {
                "source": "qdrant",
                "path": "search/_index.md",
                "relevance": 1,
            },
        ],
    },
    {
        "case_id": "qdrant_payload_index_001",
        "query": "Why should payload fields be indexed in Qdrant?",
        "category": "semantic",
        "status": "active",
        "relevant_documents": [
            {
                "source": "qdrant",
                "path": "manage-data/indexing.md",
                "relevance": 3,
            },
            {
                "source": "qdrant",
                "path": "manage-data/payload.md",
                "relevance": 2,
            },
        ],
    },
]


def main() -> None:
    OUTPUT_PATH.parent.mkdir(
        parents=True,
        exist_ok=True,
    )

    with OUTPUT_PATH.open(
        "w",
        encoding="utf-8",
    ) as file:
        for case in CASES:
            file.write(
                json.dumps(
                    case,
                    ensure_ascii=False,
                )
                + "\n"
            )

    print(f"Wrote {len(CASES)} legacy semantic cases")
    print(f"Output: {OUTPUT_PATH}")


if __name__ == "__main__":
    main()