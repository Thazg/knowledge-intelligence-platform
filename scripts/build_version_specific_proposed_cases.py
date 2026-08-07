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
        "case_id": "fastapi_pydantic_v1_v2_001",
        "query": (
            "What changes when using FastAPI with "
            "Pydantic v1 versus Pydantic v2?"
        ),
        "category": "version_specific",
        "status": "needs_review",
        "relevant_documents": [
            doc(
                "fastapi",
                "en/docs/how-to/"
                "migrate-from-pydantic-v1-to-pydantic-v2.md",
                3,
            ),
        ],
    },
    {
        "case_id": "fastapi_pydantic_migration_001",
        "query": (
            "How should FastAPI applications migrate "
            "models from Pydantic v1 to v2?"
        ),
        "category": "version_specific",
        "status": "needs_review",
        "relevant_documents": [
            doc(
                "fastapi",
                "en/docs/how-to/"
                "migrate-from-pydantic-v1-to-pydantic-v2.md",
                3,
            ),
        ],
    },
    {
        "case_id": "fastapi_deprecated_feature_001",
        "query": (
            "Which older FastAPI patterns are currently "
            "deprecated and what should replace them?"
        ),
        "category": "version_specific",
        "status": "needs_review",
        "relevant_documents": [
            doc(
                "fastapi",
                "en/docs/tutorial/schema-extra-example.md",
                3,
            ),
            doc(
                "fastapi",
                "en/docs/how-to/"
                "migrate-from-pydantic-v1-to-pydantic-v2.md",
                2,
            ),
        ],
    },
    {
        "case_id": "fastapi_python_version_001",
        "query": (
            "Which Python-version-dependent FastAPI syntax "
            "is shown differently in the documentation?"
        ),
        "category": "version_specific",
        "status": "needs_review",
        "relevant_documents": [
            doc(
                "fastapi",
                "en/docs/tutorial/dependencies/"
                "classes-as-dependencies.md",
                3,
            ),
            doc(
                "fastapi",
                "en/docs/tutorial/dependencies/index.md",
                2,
            ),
        ],
    },
    {
        "case_id": "kubernetes_deprecated_api_001",
        "query": (
            "How does Kubernetes document deprecated API "
            "versions and their replacements?"
        ),
        "category": "version_specific",
        "status": "needs_review",
        "relevant_documents": [
            doc(
                "kubernetes",
                "content/en/docs/reference/using-api/"
                "deprecation-policy.md",
                3,
            ),
            doc(
                "kubernetes",
                "content/en/docs/reference/using-api/"
                "deprecation-guide.md",
                2,
            ),
        ],
    },
    {
        "case_id": "kubernetes_removed_api_001",
        "query": (
            "Which Kubernetes APIs were removed and what "
            "versions replace them?"
        ),
        "category": "version_specific",
        "status": "needs_review",
        "relevant_documents": [
            doc(
                "kubernetes",
                "content/en/docs/reference/using-api/"
                "deprecation-guide.md",
                3,
            ),
            doc(
                "kubernetes",
                "content/en/docs/reference/using-api/"
                "deprecation-policy.md",
                1,
            ),
        ],
    },
    {
        "case_id": "kubernetes_ingress_version_001",
        "query": (
            "How did the Kubernetes Ingress API change "
            "between older beta versions and "
            "networking.k8s.io/v1?"
        ),
        "category": "version_specific",
        "status": "needs_review",
        "relevant_documents": [
            doc(
                "kubernetes",
                "content/en/docs/reference/using-api/"
                "deprecation-guide.md",
                3,
            ),
            doc(
                "kubernetes",
                "content/en/docs/concepts/"
                "services-networking/ingress.md",
                2,
            ),
            doc(
                "kubernetes",
                "content/en/docs/reference/kubernetes-api/"
                "networking/ingress-v1.md",
                1,
            ),
        ],
    },
    {
        "case_id": "kubernetes_version_skew_001",
        "query": (
            "What version skew is supported between "
            "Kubernetes components?"
        ),
        "category": "version_specific",
        "status": "needs_review",
        "relevant_documents": [
            doc(
                "kubernetes",
                "content/en/docs/setup/production-environment/"
                "tools/kubeadm/install-kubeadm.md",
                3,
            ),
            doc(
                "kubernetes",
                "content/en/docs/concepts/overview/kubectl.md",
                2,
            ),
            doc(
                "kubernetes",
                "content/en/docs/setup/production-environment/"
                "tools/kubeadm/create-cluster-kubeadm.md",
                2,
            ),
        ],
    },
    {
        "case_id": "docker_compose_version_001",
        "query": (
            "How has Docker Compose file/version handling "
            "changed in current Docker documentation?"
        ),
        "category": "version_specific",
        "status": "needs_review",
        "relevant_documents": [
            doc(
                "docker",
                "content/reference/compose-file/"
                "legacy-versions.md",
                3,
            ),
        ],
    },
    {
        "case_id": "docker_builder_version_001",
        "query": (
            "How does modern BuildKit-based Docker build "
            "behavior differ from the legacy builder?"
        ),
        "category": "version_specific",
        "status": "needs_review",
        "relevant_documents": [
            doc(
                "docker",
                "content/manuals/engine/release-notes/23.0.md",
                3,
            ),
        ],
    },
    {
        "case_id": "docker_deprecated_instruction_001",
        "query": (
            "Which Docker Engine features are deprecated "
            "or retired in current Docker documentation?"
        ),
        "category": "version_specific",
        "status": "needs_review",
        "relevant_documents": [
            doc(
                "docker",
                "content/manuals/retired.md",
                3,
            ),
        ],
    },
    {
        "case_id": "docker_api_version_001",
        "query": (
            "How does Docker handle API version "
            "compatibility between clients and daemons?"
        ),
        "category": "version_specific",
        "status": "needs_review",
        "relevant_documents": [
            doc(
                "docker",
                "content/reference/api/engine/_index.md",
                3,
            ),
        ],
    },
    {
        "case_id": "huggingface_autogptq_deprecation_001",
        "query": (
            "What should Transformers users use now that "
            "AutoGPTQ is no longer supported?"
        ),
        "category": "version_specific",
        "status": "needs_review",
        "relevant_documents": [
            doc(
                "huggingface",
                "source/en/quantization/gptq.md",
                3,
            ),
        ],
    },
    {
        "case_id": "fastapi_form_model_version_001",
        "query": (
            "From which FastAPI version are Pydantic "
            "models supported for form fields?"
        ),
        "category": "version_specific",
        "status": "needs_review",
        "relevant_documents": [
            doc(
                "fastapi",
                "en/docs/tutorial/request-form-models.md",
                3,
            ),
        ],
    },
    {
        "case_id": "fastapi_header_model_version_001",
        "query": (
            "From which FastAPI version can Pydantic "
            "models be used for header parameters?"
        ),
        "category": "version_specific",
        "status": "needs_review",
        "relevant_documents": [
            doc(
                "fastapi",
                "en/docs/tutorial/header-param-models.md",
                3,
            ),
        ],
    },
    {
        "case_id": "kubernetes_kms_version_001",
        "query": (
            "How did Kubernetes support for KMS v1 and "
            "KMS v2 change across recent releases?"
        ),
        "category": "version_specific",
        "status": "needs_review",
        "relevant_documents": [
            doc(
                "kubernetes",
                "content/en/docs/tasks/administer-cluster/"
                "kms-provider.md",
                3,
            ),
        ],
    },
    {
        "case_id": "qdrant_upgrade_001",
        "query": (
            "What should users check when upgrading "
            "Qdrant between versions?"
        ),
        "category": "version_specific",
        "status": "needs_review",
        "relevant_documents": [
            doc(
                "qdrant",
                "upgrades.md",
                3,
            ),
            doc(
                "qdrant",
                "faq/qdrant-fundamentals.md",
                2,
            ),
        ],
    },
    {
        "case_id": "kubernetes_compatibility_version_001",
        "query": (
            "What compatibility and emulation controls "
            "were introduced for Kubernetes control-plane "
            "components starting in v1.32?"
        ),
        "category": "version_specific",
        "status": "needs_review",
        "relevant_documents": [
            doc(
                "kubernetes",
                "content/en/docs/concepts/"
                "cluster-administration/"
                "compatibility-version.md",
                3,
            ),
        ],
    },
    {
        "case_id": "langgraph_api_migration_001",
        "query": (
            "Which LangGraph APIs changed or require "
            "migration in newer documentation?"
        ),
        "category": "version_specific",
        "status": "needs_review",
        "relevant_documents": [
            doc(
                "langchain",
                "python/migrate/langgraph-v1.mdx",
                3,
            ),
            doc(
                "langchain",
                "javascript/migrate/langgraph-v1.mdx",
                2,
            ),
        ],
    },
    {
        "case_id": "langgraph_deprecated_pattern_001",
        "query": (
            "Which older LangGraph workflow patterns have "
            "been replaced by newer APIs?"
        ),
        "category": "version_specific",
        "status": "needs_review",
        "relevant_documents": [
            doc(
                "langchain",
                "python/migrate/langgraph-v1.mdx",
                3,
            ),
            doc(
                "langchain",
                "langgraph/workflows-agents.mdx",
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

        relevant_documents = case["relevant_documents"]

        if not relevant_documents:
            raise RuntimeError(
                f"{case_id}: no relevant documents"
            )

        if not any(
            document["relevance"] == 3
            for document in relevant_documents
        ):
            raise RuntimeError(
                f"{case_id}: missing relevance=3 document"
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
    print("BUILD VERSION-SPECIFIC PROPOSED CASES")
    print("=" * 72)
    print(f"Cases written: {len(CASES)}")
    print(f"Output: {OUTPUT_PATH}")


if __name__ == "__main__":
    main()