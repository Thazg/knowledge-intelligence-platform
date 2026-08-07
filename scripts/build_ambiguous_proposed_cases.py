from __future__ import annotations

import json
from pathlib import Path


PROJECT_ROOT = Path(__file__).resolve().parents[1]

OUTPUT_PATH = (
    PROJECT_ROOT
    / "benchmarks"
    / "retrieval"
    / "proposed_cases.jsonl"
)


CASES = [
    {
        "case_id": "docker_context_ambiguous_001",
        "query": "How can I avoid sending unnecessary files when building an image?",
        "category": "ambiguous",
        "status": "needs_review",
        "relevant_documents": [
            {
                "source": "docker",
                "path": "content/manuals/build/cache/optimize.md",
                "relevance": 3,
            },
            {
                "source": "docker",
                "path": "content/manuals/build-cloud/optimization.md",
                "relevance": 2,
            },
        ],
    },
    {
        "case_id": "docker_cache_ambiguous_001",
        "query": "Why does rebuilding an image sometimes reuse old steps?",
        "category": "ambiguous",
        "status": "needs_review",
        "relevant_documents": [
            {
                "source": "docker",
                "path": "content/manuals/build/cache/_index.md",
                "relevance": 3,
            },
        ],
    },
    {
        "case_id": "docker_layers_ambiguous_001",
        "query": "Why does changing one build step cause later image steps to run again?",
        "category": "ambiguous",
        "status": "needs_review",
        "relevant_documents": [
            {
                "source": "docker",
                "path": "content/manuals/build/cache/_index.md",
                "relevance": 3,
            },
            {
                "source": "docker",
                "path": "content/manuals/build/cache/invalidation.md",
                "relevance": 2,
            },
        ],
    },
    {
        "case_id": "docker_small_image_ambiguous_001",
        "query": "How can I keep compilers and build tools out of my final container?",
        "category": "ambiguous",
        "status": "needs_review",
        "relevant_documents": [
            {
                "source": "docker",
                "path": "content/get-started/docker-concepts/building-images/multi-stage-builds.md",
                "relevance": 3,
            },
            {
                "source": "docker",
                "path": "content/manuals/dhi/explore/security-concepts/hardening.md",
                "relevance": 2,
            },
        ],
    },
    {
        "case_id": "kubernetes_health_ambiguous_001",
        "query": "How can Kubernetes tell whether my application is ready to receive traffic?",
        "category": "ambiguous",
        "status": "needs_review",
        "relevant_documents": [
            {
                "source": "kubernetes",
                "path": "content/en/docs/concepts/workloads/pods/probes.md",
                "relevance": 3,
            },
            {
                "source": "kubernetes",
                "path": "content/en/docs/tasks/configure-pod-container/configure-liveness-readiness-startup-probes.md",
                "relevance": 2,
            },
        ],
    },
    {
        "case_id": "kubernetes_restart_ambiguous_001",
        "query": "How can Kubernetes detect that my application is stuck and restart it?",
        "category": "ambiguous",
        "status": "needs_review",
        "relevant_documents": [
            {
                "source": "kubernetes",
                "path": "content/en/docs/concepts/workloads/pods/probes.md",
                "relevance": 3,
            },
            {
                "source": "kubernetes",
                "path": "content/en/docs/tasks/configure-pod-container/configure-liveness-readiness-startup-probes.md",
                "relevance": 2,
            },
        ],
    },
    {
        "case_id": "kubernetes_configuration_ambiguous_001",
        "query": "How can I give configuration values to containers without rebuilding the image?",
        "category": "ambiguous",
        "status": "needs_review",
        "relevant_documents": [
            {
                "source": "kubernetes",
                "path": "content/en/docs/concepts/configuration/configmap.md",
                "relevance": 3,
            },
            {
                "source": "kubernetes",
                "path": "content/en/docs/tasks/configure-pod-container/configure-pod-configmap.md",
                "relevance": 2,
            },
        ],
    },
    {
        "case_id": "kubernetes_secrets_ambiguous_001",
        "query": "Where should a Pod get sensitive configuration such as credentials?",
        "category": "ambiguous",
        "status": "needs_review",
        "relevant_documents": [
            {
                "source": "kubernetes",
                "path": "content/en/docs/concepts/configuration/secret.md",
                "relevance": 3,
            },
            {
                "source": "kubernetes",
                "path": "content/en/docs/tasks/inject-data-application/distribute-credentials-secure.md",
                "relevance": 2,
            },
        ],
    },
    {
        "case_id": "fastapi_shared_logic_ambiguous_001",
        "query": "How can multiple API endpoints reuse the same setup logic?",
        "category": "ambiguous",
        "status": "needs_review",
        "relevant_documents": [
            {
                "source": "fastapi",
                "path": "en/docs/tutorial/dependencies/index.md",
                "relevance": 3,
            },
        ],
    },
    {
        "case_id": "fastapi_after_response_ambiguous_001",
        "query": "How can my API perform work after returning the response?",
        "category": "ambiguous",
        "status": "needs_review",
        "relevant_documents": [
            {
                "source": "fastapi",
                "path": "en/docs/tutorial/background-tasks.md",
                "relevance": 3,
            },
        ],
    },
    {
        "case_id": "fastapi_validation_ambiguous_001",
        "query": "How can the API reject malformed JSON before my endpoint logic runs?",
        "category": "ambiguous",
        "status": "needs_review",
        "relevant_documents": [
            {
                "source": "fastapi",
                "path": "en/docs/tutorial/body.md",
                "relevance": 3,
            },
            {
                "source": "fastapi",
                "path": "en/docs/tutorial/handling-errors.md",
                "relevance": 2,
            },
        ],
    },
    {
        "case_id": "fastapi_cross_cutting_ambiguous_001",
        "query": "How can I run logic for every incoming request and outgoing response?",
        "category": "ambiguous",
        "status": "needs_review",
        "relevant_documents": [
            {
                "source": "fastapi",
                "path": "en/docs/tutorial/middleware.md",
                "relevance": 3,
            },
        ],
    },
    {
        "case_id": "langgraph_persistence_ambiguous_001",
        "query": "How can I save graph progress and continue it later?",
        "category": "ambiguous",
        "status": "needs_review",
        "relevant_documents": [
            {
                "source": "langchain",
                "path": "langgraph/checkpointers.mdx",
                "relevance": 3,
            },
            {
                "source": "langchain",
                "path": "langgraph/graph-api.mdx",
                "relevance": 1,
            },
        ],
    },
    {
        "case_id": "langgraph_human_ambiguous_001",
        "query": "How can a workflow stop and wait for a person before continuing?",
        "category": "ambiguous",
        "status": "needs_review",
        "relevant_documents": [
            {
                "source": "langchain",
                "path": "langgraph/interrupts.mdx",
                "relevance": 3,
            },
        ],
    },
    {
        "case_id": "langgraph_shared_data_ambiguous_001",
        "query": "How can multiple graph steps read and modify the same information?",
        "category": "ambiguous",
        "status": "needs_review",
        "relevant_documents": [
            {
                "source": "langchain",
                "path": "langgraph/use-graph-api.mdx",
                "relevance": 3,
            },
            {
                "source": "langchain",
                "path": "langgraph/graph-api.mdx",
                "relevance": 2,
            },
        ],
    },
    {
        "case_id": "langgraph_long_memory_ambiguous_001",
        "query": "How can information survive beyond a single conversation or graph run?",
        "category": "ambiguous",
        "status": "needs_review",
        "relevant_documents": [
            {
                "source": "langchain",
                "path": "langgraph/persistence.mdx",
                "relevance": 3,
            },
            {
                "source": "langchain",
                "path": "langgraph/stores.mdx",
                "relevance": 2,
            },
        ],
    },
    {
        "case_id": "qdrant_metadata_ambiguous_001",
        "query": "How can I search only vectors whose metadata matches certain conditions?",
        "category": "ambiguous",
        "status": "needs_review",
        "relevant_documents": [
            {
                "source": "qdrant",
                "path": "search/filtering.md",
                "relevance": 3,
            },
            {
                "source": "qdrant",
                "path": "manage-data/payload.md",
                "relevance": 2,
            },
        ],
    },
    {
        "case_id": "qdrant_keyword_semantic_ambiguous_001",
        "query": "How can search use both meaning and exact keyword matching?",
        "category": "ambiguous",
        "status": "needs_review",
        "relevant_documents": [
            {
                "source": "qdrant",
                "path": "search/text-search/hybrid-search.md",
                "relevance": 3,
            },
            {
                "source": "qdrant",
                "path": "search/text-search/_index.md",
                "relevance": 2,
            },
        ],
    },
    {
        "case_id": "qdrant_speed_filter_ambiguous_001",
        "query": "How can filtering remain fast when the collection becomes large?",
        "category": "ambiguous",
        "status": "needs_review",
        "relevant_documents": [
            {
                "source": "qdrant",
                "path": "manage-data/indexing.md",
                "relevance": 3,
            },
            {
                "source": "qdrant",
                "path": "manage-data/storage.md",
                "relevance": 2,
            },
        ],
    },
    {
        "case_id": "huggingface_model_input_ambiguous_001",
        "query": "How do I turn user text into something a Transformer model can process?",
        "category": "ambiguous",
        "status": "needs_review",
        "relevant_documents": [
            {
                "source": "huggingface",
                "path": "source/en/quicktour.md",
                "relevance": 3,
            },
        ],
    },
]


def validate_unique_case_ids() -> None:
    seen: set[str] = set()

    for case in CASES:
        case_id = case["case_id"]

        if case_id in seen:
            raise RuntimeError(
                f"Duplicate case_id: {case_id}"
            )

        seen.add(case_id)


def main() -> None:
    validate_unique_case_ids()

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

    print("=" * 72)
    print("BUILD AMBIGUOUS PROPOSED CASES")
    print("=" * 72)

    print(
        f"Cases written: {len(CASES)}"
    )

    print(
        f"Output: {OUTPUT_PATH}"
    )


if __name__ == "__main__":
    main()