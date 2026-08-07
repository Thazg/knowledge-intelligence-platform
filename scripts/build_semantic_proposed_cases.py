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
        "case_id": "docker_multistage_semantic_001",
        "query": "How can Docker build an application without keeping build tools in the final image?",
        "category": "semantic",
        "status": "needs_review",
        "relevant_documents": [
            {
                "source": "docker",
                "path": "content/manuals/build/building/multi-stage.md",
                "relevance": 3,
            },
            {
                "source": "docker",
                "path": "content/get-started/docker-concepts/building-images/multi-stage-builds.md",
                "relevance": 2,
            },
            {
                "source": "docker",
                "path": "content/guides/golang.md",
                "relevance": 1,
            },
        ],
    },
    {
        "case_id": "kubernetes_resource_limits_semantic_001",
        "query": "How can Kubernetes prevent one container from consuming unlimited CPU or memory?",
        "category": "semantic",
        "status": "needs_review",
        "relevant_documents": [
            {
                "source": "kubernetes",
                "path": "content/en/docs/concepts/configuration/manage-resources-containers.md",
                "relevance": 3,
            },
            {
                "source": "kubernetes",
                "path": "content/en/docs/concepts/workloads/pods/_index.md",
                "relevance": 2,
            },
            {
                "source": "kubernetes",
                "path": "content/en/docs/tasks/configure-pod-container/assign-cpu-resource.md",
                "relevance": 1,
            },
        ],
    },
    {
        "case_id": "fastapi_dependency_semantic_001",
        "query": "How can shared application logic be automatically supplied to FastAPI endpoints?",
        "category": "semantic",
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
        "case_id": "langgraph_branching_semantic_001",
        "query": "How can a LangGraph workflow choose different execution paths based on state?",
        "category": "semantic",
        "status": "needs_review",
        "relevant_documents": [
            {
                "source": "langchain",
                "path": "langgraph/choosing-apis.mdx",
                "relevance": 3,
            },
            {
                "source": "langchain",
                "path": "langgraph/use-graph-api.mdx",
                "relevance": 2,
            },
            {
                "source": "langchain",
                "path": "langchain/multi-agent/custom-workflow.mdx",
                "relevance": 1,
            },
        ],
    },
    {
        "case_id": "qdrant_similarity_semantic_001",
        "query": "How does Qdrant determine which stored vectors are closest to a query vector?",
        "category": "semantic",
        "status": "needs_review",
        "relevant_documents": [
            {
                "source": "qdrant",
                "path": "search/search.md",
                "relevance": 3,
            },
            {
                "source": "qdrant",
                "path": "overview/what-is-qdrant.md",
                "relevance": 2,
            },
            {
                "source": "qdrant",
                "path": "headless/snippets/query-points/simple-dense/_description.md",
                "relevance": 1,
            },
        ],
    },
    {
        "case_id": "huggingface_generation_semantic_001",
        "query": "How can a Transformers model generate text from an input prompt?",
        "category": "semantic",
        "status": "needs_review",
        "relevant_documents": [
            {
                "source": "huggingface",
                "path": "source/en/quicktour.md",
                "relevance": 3,
            },
            {
                "source": "huggingface",
                "path": "source/en/tasks/prompting.md",
                "relevance": 2,
            },
            {
                "source": "huggingface",
                "path": "source/en/model_doc/ernie4_5_moe.md",
                "relevance": 1,
            },
        ],
    },
    {
        "case_id": "huggingface_tokenization_semantic_001",
        "query": "How is raw text converted into model inputs for Transformers models?",
        "category": "semantic",
        "status": "needs_review",
        "relevant_documents": [
            {
                "source": "huggingface",
                "path": "source/en/quicktour.md",
                "relevance": 3,
            },
            {
                "source": "huggingface",
                "path": "source/en/glossary.md",
                "relevance": 1,
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

    print(
        f"Wrote {len(CASES)} semantic proposed cases"
    )

    print(
        f"Output: {OUTPUT_PATH}"
    )


if __name__ == "__main__":
    main()