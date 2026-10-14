import pytest

from backend.generation.source_links import source_document_url


@pytest.mark.parametrize(
    ("source", "relative_path", "expected"),
    [
        (
            "langchain",
            "concepts/memory.mdx",
            "https://github.com/langchain-ai/docs/blob/main/src/oss/concepts/memory.mdx",
        ),
        (
            "fastapi",
            "en/docs/advanced/additional-responses.md",
            "https://github.com/fastapi/fastapi/blob/master/docs/en/docs/advanced/additional-responses.md",
        ),
        (
            "docker",
            "content/get-started/docker-concepts/building-images/multi-stage-builds.md",
            "https://github.com/docker/docs/blob/main/content/get-started/docker-concepts/building-images/multi-stage-builds.md",
        ),
        (
            "kubernetes",
            "content/en/docs/concepts/architecture/controller.md",
            "https://github.com/kubernetes/website/blob/main/content/en/docs/concepts/architecture/controller.md",
        ),
        (
            "huggingface",
            "source/en/attention_interface.md",
            "https://github.com/huggingface/transformers/blob/main/docs/source/en/attention_interface.md",
        ),
        (
            "qdrant",
            "capacity-planning.md",
            "https://github.com/qdrant/landing_page/blob/master/qdrant-landing/content/documentation/capacity-planning.md",
        ),
    ],
)
def test_source_document_url_maps_v1_corpus_path(
    source: str,
    relative_path: str,
    expected: str,
) -> None:
    assert source_document_url(source, relative_path) == expected


def test_source_document_url_escapes_filename_and_rejects_unsafe_paths() -> None:
    assert source_document_url("docker", "content/my guide.md") == (
        "https://github.com/docker/docs/blob/main/content/my%20guide.md"
    )
    assert source_document_url("docker", "../README.md") is None
    assert source_document_url("docker", "/README.md") is None
    assert source_document_url("docker", "C:\\README.md") is None
    assert source_document_url("unknown", "README.md") is None
    assert source_document_url("langgraph", "llms.txt") == (
        "https://langchain-ai.github.io/langgraph/llms.txt"
    )
