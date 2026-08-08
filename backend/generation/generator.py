from __future__ import annotations

from abc import ABC, abstractmethod

from backend.generation.models import GenerationContext, GenerationResult


class LLMGenerator(ABC):
    @abstractmethod
    def generate(
        self,
        context: GenerationContext,
    ) -> GenerationResult:
        raise NotImplementedError