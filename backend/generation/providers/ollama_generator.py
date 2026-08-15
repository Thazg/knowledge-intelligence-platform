from __future__ import annotations

import re
import time
from typing import Any

import httpx

from backend.generation.generator import LLMGenerator
from backend.generation.models import Citation, GenerationContext, GenerationResult
from backend.generation.prompt_builder import PromptBuilder
from backend.core.errors import (
    DependencyResponseError,
    DependencyTimeoutError,
    DependencyUnavailableError,
)

class OllamaGenerator(LLMGenerator):
    def __init__(
        self,
        model: str = "qwen3:4b-instruct",
        base_url: str = "http://localhost:11434",
        timeout_seconds: float = 120.0,
        prompt_builder: PromptBuilder | None = None,
    ) -> None:
        self.model = model
        self.base_url = base_url.rstrip("/")
        self.timeout_seconds = timeout_seconds
        self.prompt_builder = prompt_builder or PromptBuilder()

    def generate(
        self,
        context: GenerationContext,
    ) -> GenerationResult:
        messages = self.prompt_builder.build(context)

        payload = {
            "model": self.model,
            "stream": False,
            "messages": [
                {
                    "role": "system",
                    "content": messages.system_prompt,
                },
                {
                    "role": "user",
                    "content": messages.user_prompt,
                },
            ],
            "options": {
                "temperature": 0.0,
                "num_predict": 384,
            },
        }

        start = time.perf_counter()

        try:
            with httpx.Client(
                timeout=self.timeout_seconds,
            ) as client:
                response = client.post(
                    f"{self.base_url}/api/chat",
                    json=payload,
                )

                response.raise_for_status()

        except httpx.ConnectError as exc:
            raise DependencyUnavailableError(
                "ollama"
            ) from exc

        except httpx.TimeoutException as exc:
            raise DependencyTimeoutError(
                "ollama"
            ) from exc

        except httpx.HTTPStatusError as exc:
            raise DependencyResponseError(
                "ollama"
            ) from exc

        latency_ms = (
            time.perf_counter() - start
        ) * 1000

        data: dict[str, Any] = response.json()

        answer = (
            data.get("message", {})
            .get("content", "")
            .strip()
        )

        citations = self._extract_citations(
            answer=answer,
            context=context,
        )

        prompt_tokens = self._optional_int(
            data.get("prompt_eval_count")
        )

        completion_tokens = self._optional_int(
            data.get("eval_count")
        )

        total_tokens = None

        if (
            prompt_tokens is not None
            and completion_tokens is not None
        ):
            total_tokens = (
                prompt_tokens + completion_tokens
            )

        return GenerationResult(
            query=context.query,
            answer=answer,
            citations=citations,
            sources=context.sources,
            model=self.model,
            prompt_tokens=prompt_tokens,
            completion_tokens=completion_tokens,
            total_tokens=total_tokens,
            latency_ms=latency_ms,
            metadata={
                "provider": "ollama",
                "base_url": self.base_url,
            },
        )

    @staticmethod
    def _extract_citations(
        answer: str,
        context: GenerationContext,
    ) -> list[Citation]:
        valid_sources = {
            source.citation_id: source
            for source in context.sources
        }

        citation_ids = re.findall(
            r"\[(?:SOURCE\s+)?(\d+)\]",
            answer,
            flags=re.IGNORECASE,
        )

        citations: list[Citation] = []
        seen: set[str] = set()

        for citation_id in citation_ids:
            if citation_id in seen:
                continue

            source = valid_sources.get(citation_id)

            if source is None:
                continue

            seen.add(citation_id)

            citations.append(
                Citation(
                    citation_id=citation_id,
                    document_id=source.document_id,
                    chunk_id=source.chunk_id,
                )
            )

        return citations

    @staticmethod
    def _optional_int(
        value: Any,
    ) -> int | None:
        if isinstance(value, int):
            return value

        return None