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
        "case_id": "docker_buildkit_001",
        "query": "What is Docker BuildKit and how is it used during image builds?",
        "category": "lexical",
        "status": "needs_review",
        "relevant_documents": [
            {
                "source": "docker",
                "path": "content/manuals/build/buildkit/_index.md",
                "relevance": 3,
            },
            {
                "source": "docker",
                "path": "content/manuals/build/concepts/overview.md",
                "relevance": 2,
            },
            {
                "source": "docker",
                "path": "content/manuals/build/builders/_index.md",
                "relevance": 2,
            },
        ],
    },
    {
        "case_id": "docker_copy_001",
        "query": "What does the Dockerfile COPY instruction do?",
        "category": "lexical",
        "status": "needs_review",
        "relevant_documents": [
            {
                "source": "docker",
                "path": "content/get-started/docker-concepts/building-images/writing-a-dockerfile.md",
                "relevance": 3,
            },
            {
                "source": "docker",
                "path": "content/manuals/build/concepts/dockerfile.md",
                "relevance": 2,
            },
        ],
    },
    {
        "case_id": "docker_entrypoint_001",
        "query": "What is the difference between Dockerfile ENTRYPOINT and CMD?",
        "category": "lexical",
        "status": "needs_review",
        "relevant_documents": [
            {
                "source": "docker",
                "path": "content/manuals/build/building/best-practices.md",
                "relevance": 3,
            },
            {
                "source": "docker",
                "path": "content/manuals/build/concepts/dockerfile.md",
                "relevance": 1,
            },
        ],
    },
    {
        "case_id": "kubernetes_kubectl_001",
        "query": "What does kubectl apply do?",
        "category": "lexical",
        "status": "needs_review",
        "relevant_documents": [
            {
                "source": "kubernetes",
                "path": "content/en/docs/reference/kubectl/quick-reference.md",
                "relevance": 3,
            },
            {
                "source": "kubernetes",
                "path": "content/en/docs/tasks/manage-kubernetes-objects/declarative-config.md",
                "relevance": 2,
            },
            {
                "source": "kubernetes",
                "path": "content/en/docs/concepts/workloads/management.md",
                "relevance": 2,
            },
        ],
    },
    {
        "case_id": "kubernetes_configmap_lexical_001",
        "query": "How is ConfigMap referenced from a Pod specification?",
        "category": "lexical",
        "status": "needs_review",
        "relevant_documents": [
            {
                "source": "kubernetes",
                "path": "content/en/docs/tasks/configure-pod-container/configure-pod-configmap.md",
                "relevance": 3,
            },
            {
                "source": "kubernetes",
                "path": "content/en/docs/concepts/configuration/configmap.md",
                "relevance": 2,
            },
        ],
    },
    {
        "case_id": "kubernetes_imagepullpolicy_001",
        "query": "How does imagePullPolicy control Kubernetes image pulling?",
        "category": "lexical",
        "status": "needs_review",
        "relevant_documents": [
            {
                "source": "kubernetes",
                "path": "content/en/docs/concepts/containers/images.md",
                "relevance": 3,
            },
        ],
    },
    {
        "case_id": "kubernetes_restartpolicy_001",
        "query": "What does restartPolicy control in a Kubernetes Pod?",
        "category": "lexical",
        "status": "needs_review",
        "relevant_documents": [
            {
                "source": "kubernetes",
                "path": "content/en/docs/concepts/workloads/pods/pod-lifecycle.md",
                "relevance": 3,
            },
            {
                "source": "kubernetes",
                "path": "content/en/docs/reference/kubernetes-api/core/pod-v1.md",
                "relevance": 2,
            },
        ],
    },
    {
        "case_id": "fastapi_depends_001",
        "query": "How does FastAPI's Depends function declare a dependency?",
        "category": "lexical",
        "status": "needs_review",
        "relevant_documents": [
            {
                "source": "fastapi",
                "path": "en/docs/tutorial/dependencies/index.md",
                "relevance": 3,
            },
            {
                "source": "fastapi",
                "path": "en/docs/reference/dependencies.md",
                "relevance": 2,
            },
        ],
    },
    {
        "case_id": "fastapi_backgroundtasks_lexical_001",
        "query": "How is FastAPI BackgroundTasks used inside a path operation?",
        "category": "lexical",
        "status": "needs_review",
        "relevant_documents": [
            {
                "source": "fastapi",
                "path": "en/docs/reference/background.md",
                "relevance": 3,
            },
            {
                "source": "fastapi",
                "path": "en/docs/tutorial/background-tasks.md",
                "relevance": 2,
            },
        ],
    },
    {
        "case_id": "fastapi_http_exception_001",
        "query": "How do I raise an HTTPException in FastAPI?",
        "category": "lexical",
        "status": "needs_review",
        "relevant_documents": [
            {
                "source": "fastapi",
                "path": "en/docs/reference/exceptions.md",
                "relevance": 3,
            },
        ],
    },
    {
        "case_id": "fastapi_basemodel_001",
        "query": "How is a Pydantic BaseModel used for FastAPI request bodies?",
        "category": "lexical",
        "status": "needs_review",
        "relevant_documents": [
            {
                "source": "fastapi",
                "path": "en/docs/tutorial/body.md",
                "relevance": 3,
            },
        ],
    },
    {
        "case_id": "langgraph_command_001",
        "query": "What does the LangGraph Command object do?",
        "category": "lexical",
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
                "relevance": 1,
            },
        ],
    },
    {
        "case_id": "langgraph_interrupt_lexical_001",
        "query": "How is interrupt() used inside a LangGraph node?",
        "category": "lexical",
        "status": "needs_review",
        "relevant_documents": [
            {
                "source": "langchain",
                "path": "langgraph/interrupts.mdx",
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
        "case_id": "langgraph_messagesstate_001",
        "query": "What is MessagesState in LangGraph?",
        "category": "lexical",
        "status": "needs_review",
        "relevant_documents": [
            {
                "source": "langchain",
                "path": "langgraph/graph-api.mdx",
                "relevance": 3,
            },
            {
                "source": "langchain",
                "path": "langgraph/use-graph-api.mdx",
                "relevance": 2,
            },
        ],
    },
    {
        "case_id": "qdrant_hnsw_001",
        "query": "How is the HNSW index configured in Qdrant?",
        "category": "lexical",
        "status": "needs_review",
        "relevant_documents": [
            {
                "source": "qdrant",
                "path": "manage-data/indexing.md",
                "relevance": 3,
            },
            {
                "source": "qdrant",
                "path": "headless/snippets/create-collection/with-disabled-global-hnsw/_description.md",
                "relevance": 2,
            },
        ],
    },
    {
        "case_id": "qdrant_payload_index_lexical_001",
        "query": "How do I create a Qdrant payload index?",
        "category": "lexical",
        "status": "needs_review",
        "relevant_documents": [
            {
                "source": "qdrant",
                "path": "manage-data/indexing.md",
                "relevance": 3,
            },
            {
                "source": "qdrant",
                "path": "headless/snippets/create-payload-index/simple-keyword/_description.md",
                "relevance": 2,
            },
        ],
    },
    {
        "case_id": "huggingface_autotokenizer_001",
        "query": "How is AutoTokenizer.from_pretrained() used?",
        "category": "lexical",
        "status": "needs_review",
        "relevant_documents": [
            {
                "source": "huggingface",
                "path": "source/en/fast_tokenizers.md",
                "relevance": 3,
            },
            {
                "source": "huggingface",
                "path": "source/en/main_classes/tokenizer.md",
                "relevance": 2,
            },
        ],
    },
    {
        "case_id": "huggingface_automodel_001",
        "query": "What does AutoModel.from_pretrained() load?",
        "category": "lexical",
        "status": "needs_review",
        "relevant_documents": [
            {
                "source": "huggingface",
                "path": "source/en/models.md",
                "relevance": 3,
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
        f"Wrote {len(CASES)} lexical proposed cases"
    )

    print(
        f"Output: {OUTPUT_PATH}"
    )


if __name__ == "__main__":
    main()