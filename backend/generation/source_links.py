"""Links from indexed documentation paths to public upstream sources.

The v1 corpus stores a source label and a path relative to that source's
ingestion root. Constructing links at response time also covers Qdrant Cloud
collections that were created before the API returned source URLs.
"""

from __future__ import annotations

from pathlib import PurePosixPath
from urllib.parse import quote

_SOURCE_REPOSITORIES = {
    "langchain": ("langchain-ai/docs", "main", "src/oss"),
    "fastapi": ("fastapi/fastapi", "master", "docs"),
    "docker": ("docker/docs", "main", ""),
    "kubernetes": ("kubernetes/website", "main", ""),
    "huggingface": ("huggingface/transformers", "main", "docs"),
    "qdrant": (
        "qdrant/landing_page",
        "master",
        "qdrant-landing/content/documentation",
    ),
}


def source_document_url(
    source: str | None,
    relative_path: str | None,
) -> str | None:
    """Return a public source link for a known, safe corpus path."""
    if not source or not relative_path:
        return None

    repository = _SOURCE_REPOSITORIES.get(source.casefold())
    if source.casefold() == "langgraph" and relative_path == "llms.txt":
        # The indexed file is no longer at src/langgraph/llms.txt in the
        # upstream repository, but its public LangGraph index remains live.
        return "https://langchain-ai.github.io/langgraph/llms.txt"
    if repository is None:
        return None

    normalized = relative_path.replace("\\", "/")
    path = PurePosixPath(normalized)
    if (
        path.is_absolute()
        or not path.parts
        or any(part in {".", ".."} or ":" in part for part in path.parts)
    ):
        return None

    repo_name, branch, docs_root = repository
    components = [*PurePosixPath(docs_root).parts, *path.parts]
    encoded_path = "/".join(quote(part, safe="") for part in components)
    return f"https://github.com/{repo_name}/blob/{branch}/{encoded_path}"
