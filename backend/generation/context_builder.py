from __future__ import annotations

from collections.abc import Callable
from typing import Any

from backend.generation.models import GenerationContext, SourceReference
from backend.retrieval.models import RetrievalResult


class ContextBuilder:
    def __init__(
        self,
        max_context_tokens: int = 6000,
        max_sources: int = 8,
        tokenizer: Callable[[str], int] | None = None,
    ) -> None:
        if max_context_tokens <= 0:
            raise ValueError("max_context_tokens must be > 0")

        if max_sources <= 0:
            raise ValueError("max_sources must be > 0")

        self.max_context_tokens = max_context_tokens
        self.max_sources = max_sources
        self.tokenizer = tokenizer

    def build(
        self,
        query: str,
        results: list[RetrievalResult],
    ) -> GenerationContext:
        selected_sources: list[SourceReference] = []
        context_blocks: list[str] = []

        seen_chunks: set[str] = set()
        total_tokens = 0

        for result in results:
            if len(selected_sources) >= self.max_sources:
                break

            metadata = self._get_metadata(result)

            document_id = str(
                self._get_value(result, metadata, "document_id", "")
            )
            chunk_id = str(
                self._get_value(result, metadata, "chunk_id", "")
            )

            # Prevent duplicate chunks from entering the generation context.
            dedup_key = chunk_id or f"{document_id}:{id(result)}"

            if dedup_key in seen_chunks:
                continue

            content = self._extract_content(result, metadata)

            if not content:
                continue

            citation_id = str(len(selected_sources) + 1)

            title = self._optional_str(
                self._get_value(result, metadata, "title")
            )
            source = self._optional_str(
                self._get_value(result, metadata, "source")
            )
            url = self._optional_str(
                self._get_value(result, metadata, "url")
            )

            source_reference = SourceReference(
                citation_id=citation_id,
                document_id=document_id,
                chunk_id=chunk_id,
                title=title,
                source=source,
                url=url,
                metadata=metadata,
            )

            block = self._format_source(
                source=source_reference,
                content=content,
            )

            block_tokens = self._count_tokens(block)

            if total_tokens + block_tokens > self.max_context_tokens:
                continue

            seen_chunks.add(dedup_key)
            selected_sources.append(source_reference)
            context_blocks.append(block)

            total_tokens += block_tokens

        context_text = "\n\n".join(context_blocks)

        return GenerationContext(
            query=query,
            context_text=context_text,
            sources=selected_sources,
            token_count=total_tokens,
        )

    def _extract_content(
        self,
        result: RetrievalResult,
        metadata: dict[str, Any],
    ) -> str:
        """
        Resolve chunk text without tightly coupling ContextBuilder
        to a single RetrievalResult representation.
        """
        for field_name in ("content", "text", "chunk_text"):
            value = getattr(result, field_name, None)

            if isinstance(value, str) and value.strip():
                return value.strip()

        for field_name in ("content", "text", "chunk_text"):
            value = metadata.get(field_name)

            if isinstance(value, str) and value.strip():
                return value.strip()

        return ""

    @staticmethod
    def _get_metadata(
        result: RetrievalResult,
    ) -> dict[str, Any]:
        metadata = getattr(result, "metadata", None)

        if isinstance(metadata, dict):
            return dict(metadata)

        return {}

    @staticmethod
    def _get_value(
        result: RetrievalResult,
        metadata: dict[str, Any],
        field_name: str,
        default: Any = None,
    ) -> Any:
        value = getattr(result, field_name, None)

        if value is not None:
            return value

        return metadata.get(field_name, default)

    @staticmethod
    def _optional_str(value: Any) -> str | None:
        if value is None:
            return None

        value = str(value).strip()

        return value or None

    def _count_tokens(self, text: str) -> int:
        if self.tokenizer is not None:
            return self.tokenizer(text)

        # Temporary deterministic approximation.
        # Replace with the generator model tokenizer later.
        return max(1, len(text) // 4)

    @staticmethod
    def _format_source(
        source: SourceReference,
        content: str,
    ) -> str:
        lines = [
            f"[SOURCE {source.citation_id}]",
        ]

        if source.title:
            lines.append(f"title: {source.title}")

        if source.source:
            lines.append(f"source: {source.source}")

        if source.url:
            lines.append(f"url: {source.url}")

        if source.document_id:
            lines.append(f"document_id: {source.document_id}")

        if source.chunk_id:
            lines.append(f"chunk_id: {source.chunk_id}")

        lines.extend(
            [
                "",
                content,
            ]
        )

        return "\n".join(lines)