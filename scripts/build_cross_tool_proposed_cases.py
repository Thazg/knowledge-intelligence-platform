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


def doc(
    source: str,
    path: str,
    relevance: int,
) -> dict:
    return {
        "source": source,
        "path": path,
        "relevance": relevance,
    }


CASES = [
    {
        "case_id": "fastapi_docker_001",
        "query": (
            "How should I containerize a FastAPI "
            "application with Docker?"
        ),
        "category": "cross_tool",
        "status": "needs_review",
        "relevant_documents": [
            doc(
                "fastapi",
                "en/docs/deployment/docker.md",
                3,
            ),
            doc(
                "docker",
                "content/guides/python.md",
                2,
            ),
        ],
    },
    {
        "case_id": "fastapi_kubernetes_001",
        "query": (
            "How should I deploy a FastAPI "
            "application on Kubernetes?"
        ),
        "category": "cross_tool",
        "status": "needs_review",
        "relevant_documents": [
            doc(
                "fastapi",
                "en/docs/deployment/concepts.md",
                3,
            ),
            doc(
                "docker",
                "content/guides/kube-deploy.md",
                2,
            ),
            doc(
                "kubernetes",
                "content/en/docs/tutorials/"
                "kubernetes-basics/deploy-app/"
                "deploy-intro.md",
                2,
            ),
        ],
    },
    {
        "case_id": "fastapi_docker_kubernetes_001",
        "query": (
            "How can I package a FastAPI service "
            "in Docker and deploy it to Kubernetes?"
        ),
        "category": "cross_tool",
        "status": "needs_review",
        "relevant_documents": [
            doc(
                "fastapi",
                "en/docs/deployment/docker.md",
                3,
            ),
            doc(
                "docker",
                "content/guides/kube-deploy.md",
                3,
            ),
            doc(
                "fastapi",
                "en/docs/deployment/concepts.md",
                2,
            ),
        ],
    },
    {
        "case_id": "fastapi_qdrant_001",
        "query": (
            "How can a FastAPI endpoint query "
            "vectors stored in Qdrant?"
        ),
        "category": "cross_tool",
        "status": "needs_review",
        "relevant_documents": [
            doc(
                "qdrant",
                "tutorials-develop/neural-search.md",
                3,
            ),
        ],
    },
    {
        "case_id": "fastapi_huggingface_001",
        "query": (
            "How can Transformers model inference "
            "be wrapped behind a FastAPI endpoint?"
        ),
        "category": "cross_tool",
        "status": "needs_review",
        "relevant_documents": [
            doc(
                "huggingface",
                "source/en/quicktour.md",
                3,
            ),
            doc(
                "fastapi",
                "en/docs/tutorial/first-steps.md",
                2,
            ),
        ],
    },
    {
        "case_id": "langgraph_fastapi_001",
        "query": (
            "How can I expose a LangGraph workflow "
            "through a FastAPI endpoint?"
        ),
        "category": "cross_tool",
        "status": "needs_review",
        "relevant_documents": [
            doc(
                "langchain",
                "langchain/frontend/"
                "integrations/copilotkit.mdx",
                3,
            ),
        ],
    },
    {
        "case_id": "langgraph_qdrant_001",
        "query": (
            "How can a LangGraph workflow retrieve "
            "information from Qdrant?"
        ),
        "category": "cross_tool",
        "status": "needs_review",
        "relevant_documents": [
            doc(
                "qdrant",
                "frameworks/langgraph.md",
                3,
            ),
            doc(
                "qdrant",
                "tutorials-build-essentials/"
                "agentic-rag-langgraph.md",
                2,
            ),
        ],
    },
    {
        "case_id": "langgraph_fastapi_qdrant_001",
        "query": (
            "How can a FastAPI service run a "
            "LangGraph workflow that retrieves "
            "context from Qdrant?"
        ),
        "category": "cross_tool",
        "status": "needs_review",
        "relevant_documents": [
            doc(
                "qdrant",
                "tutorials-build-essentials/"
                "agentic-rag-langgraph.md",
                3,
            ),
            doc(
                "langchain",
                "langchain/frontend/"
                "integrations/copilotkit.mdx",
                2,
            ),
            doc(
                "qdrant",
                "tutorials-develop/neural-search.md",
                2,
            ),
        ],
    },
    {
        "case_id": "langgraph_docker_001",
        "query": (
            "How can I package a LangGraph "
            "application in a Docker container?"
        ),
        "category": "cross_tool",
        "status": "needs_review",
        "relevant_documents": [
            doc(
                "langchain",
                "langgraph/application-structure.mdx",
                3,
            ),
            doc(
                "langchain",
                "deepagents/going-to-production.mdx",
                2,
            ),
        ],
    },
    {
        "case_id": "langgraph_kubernetes_001",
        "query": (
            "How can a LangGraph application be "
            "packaged as a service and deployed as "
            "a Kubernetes workload?"
        ),
        "category": "cross_tool",
        "status": "needs_review",
        "relevant_documents": [
            doc(
                "langchain",
                "langgraph/application-structure.mdx",
                3,
            ),
            doc(
                "kubernetes",
                "content/en/docs/tutorials/"
                "kubernetes-basics/deploy-app/"
                "deploy-intro.md",
                2,
            ),
        ],
    },
    {
        "case_id": "huggingface_qdrant_001",
        "query": (
            "How can embeddings from a Transformers "
            "model be stored and searched in Qdrant?"
        ),
        "category": "cross_tool",
        "status": "needs_review",
        "relevant_documents": [
            doc(
                "qdrant",
                "tutorials-basics/"
                "search-beginners-local.md",
                3,
            ),
            doc(
                "qdrant",
                "frameworks/txtai.md",
                2,
            ),
        ],
    },
    {
        "case_id": "huggingface_fastapi_qdrant_001",
        "query": (
            "How can FastAPI generate embeddings "
            "with Transformers and search them "
            "in Qdrant?"
        ),
        "category": "cross_tool",
        "status": "needs_review",
        "relevant_documents": [
            doc(
                "qdrant",
                "tutorials-develop/neural-search.md",
                3,
            ),
            doc(
                "qdrant",
                "tutorials-develop/"
                "hybrid-search-fastembed.md",
                2,
            ),
            doc(
                "huggingface",
                "source/en/quicktour.md",
                1,
            ),
        ],
    },
    {
        "case_id": "huggingface_docker_001",
        "query": (
            "How can a Transformers inference "
            "application be packaged with Docker?"
        ),
        "category": "cross_tool",
        "status": "needs_review",
        "relevant_documents": [
            doc(
                "docker",
                "content/guides/"
                "text-summarization.md",
                3,
            ),
            doc(
                "huggingface",
                "source/en/serve-cli/serving.md",
                2,
            ),
        ],
    },
    {
        "case_id": "huggingface_kubernetes_001",
        "query": (
            "How can a containerized Transformers "
            "inference service run on Kubernetes?"
        ),
        "category": "cross_tool",
        "status": "needs_review",
        "relevant_documents": [
            doc(
                "huggingface",
                "source/en/serve-cli/serving.md",
                3,
            ),
            doc(
                "kubernetes",
                "content/en/docs/tutorials/"
                "kubernetes-basics/deploy-app/"
                "deploy-intro.md",
                2,
            ),
            doc(
                "kubernetes",
                "content/en/docs/concepts/"
                "services-networking/service.md",
                2,
            ),
        ],
    },
    {
        "case_id": "docker_kubernetes_001",
        "query": (
            "How does a Docker container image "
            "become a running workload in Kubernetes?"
        ),
        "category": "cross_tool",
        "status": "needs_review",
        "relevant_documents": [
            doc(
                "kubernetes",
                "content/en/docs/concepts/"
                "containers/images.md",
                3,
            ),
            doc(
                "kubernetes",
                "content/en/docs/concepts/"
                "workloads/_index.md",
                3,
            ),
        ],
    },
    {
        "case_id": "docker_kubernetes_config_001",
        "query": (
            "How should configuration be separated "
            "between a Docker image and Kubernetes "
            "runtime configuration?"
        ),
        "category": "cross_tool",
        "status": "needs_review",
        "relevant_documents": [
            doc(
                "kubernetes",
                "content/en/docs/concepts/"
                "containers/images.md",
                3,
            ),
            doc(
                "docker",
                "content/manuals/compose/"
                "bridge/customize.md",
                2,
            ),
        ],
    },
    {
        "case_id": "docker_kubernetes_health_001",
        "query": (
            "How should container health behavior "
            "be configured when running Docker "
            "images in Kubernetes?"
        ),
        "category": "cross_tool",
        "status": "needs_review",
        "relevant_documents": [
            doc(
                "kubernetes",
                "content/en/docs/concepts/"
                "workloads/pods/probes.md",
                3,
            ),
            doc(
                "fastapi",
                "en/docs/deployment/docker.md",
                2,
            ),
        ],
    },
    {
        "case_id": "qdrant_docker_001",
        "query": (
            "How can Qdrant be run as a Docker "
            "container with persistent storage?"
        ),
        "category": "cross_tool",
        "status": "needs_review",
        "relevant_documents": [
            doc(
                "qdrant",
                "installation.md",
                3,
            ),
            doc(
                "qdrant",
                "quickstart.md",
                2,
            ),
        ],
    },
    {
        "case_id": "qdrant_kubernetes_001",
        "query": (
            "How could a Qdrant service be deployed "
            "and exposed in Kubernetes?"
        ),
        "category": "cross_tool",
        "status": "needs_review",
        "relevant_documents": [
            doc(
                "qdrant",
                "hybrid-cloud/"
                "hybrid-cloud-cluster-creation.md",
                3,
            ),
            doc(
                "qdrant",
                "installation.md",
                2,
            ),
        ],
    },
    {
        "case_id": "rag_stack_001",
        "query": (
            "How can FastAPI, LangGraph, "
            "Transformers, and Qdrant work together "
            "in a RAG service?"
        ),
        "category": "cross_tool",
        "status": "needs_review",
        "relevant_documents": [
            doc(
                "qdrant",
                "tutorials-build-essentials/"
                "agentic-rag-langgraph.md",
                3,
            ),
            doc(
                "qdrant",
                "tutorials-develop/neural-search.md",
                2,
            ),
            doc(
                "langchain",
                "python/integrations/"
                "vectorstores/qdrant.mdx",
                2,
            ),
            doc(
                "huggingface",
                "source/en/quicktour.md",
                1,
            ),
        ],
    },
]


def validate_cases() -> None:
    if len(CASES) != 20:
        raise RuntimeError(
            f"Expected 20 cases, got {len(CASES)}"
        )

    seen: set[str] = set()

    for case in CASES:
        case_id = case["case_id"]

        if case_id in seen:
            raise RuntimeError(
                f"Duplicate case_id: {case_id}"
            )

        seen.add(case_id)

        if case["category"] != "cross_tool":
            raise RuntimeError(
                f"{case_id}: invalid category"
            )

        relevant_documents = (
            case["relevant_documents"]
        )

        if not relevant_documents:
            raise RuntimeError(
                f"{case_id}: no relevant documents"
            )

        if not any(
            document["relevance"] == 3
            for document in relevant_documents
        ):
            raise RuntimeError(
                f"{case_id}: missing relevance=3"
            )

        seen_docs: set[tuple[str, str]] = set()

        for document in relevant_documents:
            key = (
                document["source"],
                document["path"],
            )

            if key in seen_docs:
                raise RuntimeError(
                    f"{case_id}: duplicate document {key}"
                )

            seen_docs.add(key)

            if document["relevance"] not in {
                1,
                2,
                3,
            }:
                raise RuntimeError(
                    f"{case_id}: invalid relevance"
                )


def main() -> None:
    validate_cases()

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
    print("BUILD CROSS-TOOL PROPOSED CASES")
    print("=" * 72)
    print(f"Cases written: {len(CASES)}")
    print(f"Output: {OUTPUT_PATH}")


if __name__ == "__main__":
    main()