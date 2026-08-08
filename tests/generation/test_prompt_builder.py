from backend.generation.models import GenerationContext, SourceReference
from backend.generation.prompt_builder import PromptBuilder


def test_prompt_builder_with_context() -> None:
    context = GenerationContext(
        query="What does Kubernetes Deployment manage?",
        context_text=(
            "[SOURCE 1]\n"
            "title: Kubernetes Documentation\n\n"
            "A Deployment manages a set of Pods."
        ),
        sources=[
            SourceReference(
                citation_id="1",
                document_id="doc-1",
                chunk_id="chunk-1",
                title="Kubernetes Documentation",
                source="kubernetes",
            )
        ],
        token_count=20,
    )

    builder = PromptBuilder()
    messages = builder.build(context)

    assert "using only the provided sources" in messages.system_prompt
    assert "What does Kubernetes Deployment manage?" in messages.user_prompt
    assert "[SOURCE 1]" in messages.user_prompt
    assert "[1]" in messages.user_prompt


def test_prompt_builder_without_context() -> None:
    context = GenerationContext(
        query="Unknown question",
        context_text="",
        sources=[],
        token_count=0,
    )

    builder = PromptBuilder()
    messages = builder.build(context)

    assert "No supporting sources were retrieved." in messages.user_prompt
    assert "insufficient" in messages.user_prompt.lower()