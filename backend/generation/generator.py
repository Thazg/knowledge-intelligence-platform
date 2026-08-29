from __future__ import annotations

from abc import ABC, abstractmethod
from collections.abc import Iterator

from backend.generation.models import (
    GenerationComplete,
    GenerationContext,
    GenerationDelta,
    GenerationResult,
    GeneratorStreamEvent,
)


class LLMGenerator(ABC):
    @abstractmethod
    def generate(
        self,
        context: GenerationContext,
    ) -> GenerationResult:
        raise NotImplementedError

    def stream(
        self,
        context: GenerationContext,
    ) -> Iterator[GeneratorStreamEvent]:
        """Yield a completed answer once when native streaming is unavailable."""
        result = self.generate(context)

        if result.answer:
            yield GenerationDelta(
                text=result.answer,
            )

        yield GenerationComplete(
            result=result,
        )
