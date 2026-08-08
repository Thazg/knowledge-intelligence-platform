from __future__ import annotations

import time
from dataclasses import replace
from typing import Protocol

from backend.generation.context_builder import ContextBuilder
from backend.generation.generator import LLMGenerator
from backend.generation.models import GenerationResult
from backend.retrieval.models import RetrievalResult


class RetrieverProtocol(Protocol):
    def retrieve(
        self,
        query: str,
        top_k: int,
        **kwargs: object,
    ) -> list[RetrievalResult]:
        ...


class RAGPipeline:
    def __init__(
        self,
        retriever: RetrieverProtocol,
        context_builder: ContextBuilder,
        generator: LLMGenerator,
        top_k: int = 10,
    ) -> None:
        if top_k <= 0:
            raise ValueError("top_k must be > 0")

        self.retriever = retriever
        self.context_builder = context_builder
        self.generator = generator
        self.top_k = top_k

    def run(
        self,
        query: str,
    ) -> GenerationResult:
        query = query.strip()

        if not query:
            raise ValueError("query must not be empty")

        pipeline_start = time.perf_counter()

        retrieval_start = time.perf_counter()

        results = self.retriever.retrieve(
            query=query,
            top_k=self.top_k,
        )

        retrieval_latency_ms = (
            time.perf_counter() - retrieval_start
        ) * 1000

        context_start = time.perf_counter()

        context = self.context_builder.build(
            query=query,
            results=results,
        )

        context_latency_ms = (
            time.perf_counter() - context_start
        ) * 1000

        generation_start = time.perf_counter()

        result = self.generator.generate(context)

        generation_stage_latency_ms = (
            time.perf_counter() - generation_start
        ) * 1000

        end_to_end_latency_ms = (
            time.perf_counter() - pipeline_start
        ) * 1000

        metadata = dict(result.metadata)

        metadata.update(
            {
                "retrieval_latency_ms": retrieval_latency_ms,
                "context_build_latency_ms": context_latency_ms,
                "generation_stage_latency_ms": generation_stage_latency_ms,
                "end_to_end_latency_ms": end_to_end_latency_ms,
                "retrieved_results": len(results),
                "context_sources": len(context.sources),
                "context_tokens": context.token_count,
                "cited_sources": len(result.citations),
            }
        )

        return replace(
            result,
            metadata=metadata,
        )