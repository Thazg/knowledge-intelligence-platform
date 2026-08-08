from __future__ import annotations

from backend.generation.generator import LLMGenerator
from backend.generation.models import Citation, GenerationContext, GenerationResult


class FakeGenerator(LLMGenerator):
    """
    Deterministic generator used for pipeline tests.

    It does not call any external LLM.
    """

    def __init__(
        self,
        model: str = "fake-generator-v1",
    ) -> None:
        self.model = model

    def generate(
        self,
        context: GenerationContext,
    ) -> GenerationResult:
        if not context.sources:
            return GenerationResult(
                query=context.query,
                answer=(
                    "The available evidence is insufficient "
                    "to answer the question reliably."
                ),
                citations=[],
                sources=[],
                model=self.model,
                prompt_tokens=context.token_count,
                completion_tokens=None,
                total_tokens=context.token_count,
                latency_ms=0.0,
                metadata={
                    "generator": "fake",
                    "grounded": False,
                },
            )

        first_source = context.sources[0]

        citation = Citation(
            citation_id=first_source.citation_id,
            document_id=first_source.document_id,
            chunk_id=first_source.chunk_id,
        )

        answer = (
            f"The retrieved evidence provides information "
            f"relevant to the question [{first_source.citation_id}]."
        )

        return GenerationResult(
            query=context.query,
            answer=answer,
            citations=[citation],
            sources=context.sources,
            model=self.model,
            prompt_tokens=context.token_count,
            completion_tokens=None,
            total_tokens=context.token_count,
            latency_ms=0.0,
            metadata={
                "generator": "fake",
                "grounded": True,
            },
        )