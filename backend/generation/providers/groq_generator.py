from __future__ import annotations

import re
import threading
import time
from typing import Any

import httpx

from backend.core.errors import (
    DependencyBusyError,
    DependencyResponseError,
    DependencyTimeoutError,
    DependencyUnavailableError,
)
from backend.generation.generator import LLMGenerator
from backend.generation.models import (
    Citation,
    GenerationContext,
    GenerationResult,
)
from backend.generation.prompt_builder import PromptBuilder


class GroqGenerator(LLMGenerator):
    GPT_OSS_MODEL_PREFIX = "openai/gpt-oss-"

    def __init__(
        self,
        *,
        model: str,
        api_key: str,
        base_url: str = (
            "https://api.groq.com/openai/v1"
        ),
        timeout_seconds: float = 120.0,
        max_concurrent_generations: int = 1,
        prompt_builder: PromptBuilder | None = None,
    ) -> None:
        if not model.strip():
            raise ValueError(
                "model must not be empty."
            )

        if not api_key.strip():
            raise ValueError(
                "api_key must not be empty."
            )

        if not base_url.strip():
            raise ValueError(
                "base_url must not be empty."
            )

        if timeout_seconds <= 0:
            raise ValueError(
                "timeout_seconds must be "
                "greater than 0."
            )

        if max_concurrent_generations <= 0:
            raise ValueError(
                "max_concurrent_generations must "
                "be greater than 0."
            )

        self.model = model
        self.api_key = api_key
        self.base_url = base_url.rstrip("/")
        self.timeout_seconds = timeout_seconds
        self.prompt_builder = (
            prompt_builder
            or PromptBuilder()
        )
        self._generation_slots = (
            threading.BoundedSemaphore(
                value=(
                    max_concurrent_generations
                ),
            )
        )

    def generate(
        self,
        context: GenerationContext,
    ) -> GenerationResult:
        messages = self.prompt_builder.build(
            context
        )

        payload = self._build_payload(
            system_prompt=(
                messages.system_prompt
            ),
            user_prompt=(
                messages.user_prompt
            ),
        )

        headers = {
            "Authorization": (
                f"Bearer {self.api_key}"
            ),
            "Content-Type": (
                "application/json"
            ),
        }

        slot_acquired = (
            self._generation_slots.acquire(
                blocking=False,
            )
        )

        if not slot_acquired:
            raise DependencyBusyError(
                "groq"
            )

        start = time.perf_counter()

        try:
            try:
                with httpx.Client(
                    timeout=self.timeout_seconds,
                ) as client:
                    response = client.post(
                        (
                            f"{self.base_url}"
                            "/chat/completions"
                        ),
                        headers=headers,
                        json=payload,
                    )
                    response.raise_for_status()

            except httpx.ConnectError as exc:
                raise (
                    DependencyUnavailableError(
                        "groq"
                    )
                ) from exc

            except httpx.TimeoutException as exc:
                raise DependencyTimeoutError(
                    "groq"
                ) from exc

            except httpx.HTTPStatusError as exc:
                raise DependencyResponseError(
                    "groq"
                ) from exc

            try:
                data: dict[str, Any] = (
                    response.json()
                )

                choices = data.get(
                    "choices"
                )

                if (
                    not isinstance(
                        choices,
                        list,
                    )
                    or not choices
                ):
                    raise ValueError(
                        "Groq response contains "
                        "no choices."
                    )

                first_choice = choices[0]

                if not isinstance(
                    first_choice,
                    dict,
                ):
                    raise ValueError(
                        "Groq response choice "
                        "has invalid shape."
                    )

                message = first_choice.get(
                    "message"
                )

                if not isinstance(
                    message,
                    dict,
                ):
                    raise ValueError(
                        "Groq response contains "
                        "no message."
                    )

                raw_answer = message.get(
                    "content"
                )

                if not isinstance(
                    raw_answer,
                    str,
                ):
                    raise ValueError(
                        "Groq response content "
                        "is not text."
                    )

                answer = raw_answer.strip()

                if not answer:
                    raise ValueError(
                        "Groq response content "
                        "is empty."
                    )

            except (
                ValueError,
                TypeError,
            ) as exc:
                raise DependencyResponseError(
                    "groq"
                ) from exc

        finally:
            self._generation_slots.release()

        latency_ms = (
            time.perf_counter()
            - start
        ) * 1000

        citations = self._extract_citations(
            answer=answer,
            context=context,
        )

        usage = data.get(
            "usage",
            {},
        )

        if not isinstance(
            usage,
            dict,
        ):
            usage = {}

        prompt_tokens = self._optional_int(
            usage.get("prompt_tokens")
        )
        completion_tokens = (
            self._optional_int(
                usage.get(
                    "completion_tokens"
                )
            )
        )
        total_tokens = self._optional_int(
            usage.get("total_tokens")
        )

        if (
            total_tokens is None
            and prompt_tokens is not None
            and completion_tokens is not None
        ):
            total_tokens = (
                prompt_tokens
                + completion_tokens
            )

        return GenerationResult(
            query=context.query,
            answer=answer,
            citations=citations,
            sources=context.sources,
            model=self.model,
            prompt_tokens=prompt_tokens,
            completion_tokens=(
                completion_tokens
            ),
            total_tokens=total_tokens,
            latency_ms=latency_ms,
            metadata={
                "provider": "groq",
                "base_url": self.base_url,
            },
        )

    def _build_payload(
        self,
        *,
        system_prompt: str,
        user_prompt: str,
    ) -> dict[str, Any]:
        payload: dict[str, Any] = {
            "model": self.model,
            "stream": False,
            "messages": [
                {
                    "role": "system",
                    "content": system_prompt,
                },
                {
                    "role": "user",
                    "content": user_prompt,
                },
            ],
            "temperature": 0.0,
            "max_completion_tokens": 1024,
        }

        if self.model.startswith(
            self.GPT_OSS_MODEL_PREFIX
        ):
            payload.update(
                {
                    "reasoning_effort": "low",
                    "include_reasoning": False,
                }
            )

        return payload

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

            source = valid_sources.get(
                citation_id
            )

            if source is None:
                continue

            seen.add(citation_id)

            citations.append(
                Citation(
                    citation_id=(
                        citation_id
                    ),
                    document_id=(
                        source.document_id
                    ),
                    chunk_id=(
                        source.chunk_id
                    ),
                )
            )

        return citations

    @staticmethod
    def _optional_int(
        value: Any,
    ) -> int | None:
        if isinstance(
            value,
            int,
        ):
            return value

        return None