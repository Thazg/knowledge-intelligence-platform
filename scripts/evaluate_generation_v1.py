from __future__ import annotations

import argparse
import json
import time
from pathlib import Path

from backend.chunking.serializer import ChunkSerializer
from backend.embedding.embedder import LocalEmbedder
from backend.generation.context_builder import ContextBuilder
from backend.generation.providers.ollama_generator import OllamaGenerator
from backend.generation.rag_pipeline import RAGPipeline
from backend.retrieval.bm25_retriever import BM25Retriever
from backend.retrieval.dense_retriever import DenseRetriever
from backend.retrieval.hybrid_retriever import HybridRetriever
from backend.vector_store.qdrant_store import QdrantVectorStore


CASES_PATH = Path("benchmarks/generation/cases_v1.jsonl")
DEFAULT_OUTPUT_PATH = Path("benchmarks/generation/results_v3.jsonl")

CHUNKS_PATH = Path("data/processed/chunks_fixed.jsonl")

QDRANT_COLLECTION = "enterprise_knowledge_fixed_bge_small"
EMBEDDING_MODEL = "BAAI/bge-small-en-v1.5"
GENERATION_MODEL = "qwen3:4b-instruct"


def load_cases(path: Path) -> list[dict]:
    cases: list[dict] = []

    with path.open(
        "r",
        encoding="utf-8",
    ) as file:
        for line_number, line in enumerate(file, start=1):
            line = line.strip()

            if not line:
                continue

            try:
                case = json.loads(line)
            except json.JSONDecodeError as exc:
                raise ValueError(
                    f"Invalid JSON at line {line_number}: {exc}"
                ) from exc

            cases.append(case)

    return cases


def build_pipeline() -> RAGPipeline:
    print("Loading chunks...")

    serializer = ChunkSerializer()
    chunks = serializer.load_jsonl(CHUNKS_PATH)

    print(f"Loaded {len(chunks)} chunks.")

    print("Loading embedding model...")

    embedder = LocalEmbedder(
        model_name=EMBEDDING_MODEL,
    )

    print("Connecting to Qdrant...")

    vector_store = QdrantVectorStore(
        collection_name=QDRANT_COLLECTION,
        vector_size=embedder.dimension,
    )

    print("Building retrievers...")

    dense = DenseRetriever(
        embedder=embedder,
        vector_store=vector_store,
    )

    bm25 = BM25Retriever(
        chunks=chunks,
    )

    weighted_rrf = HybridRetriever(
        dense_retriever=dense,
        bm25_retriever=bm25,
        dense_weight=0.7,
        bm25_weight=0.3,
        rrf_k=60,
    )

    context_builder = ContextBuilder(
        max_context_tokens=4000,
        max_sources=6,
    )

    generator = OllamaGenerator(
        model=GENERATION_MODEL,
    )

    return RAGPipeline(
        retriever=weighted_rrf,
        context_builder=context_builder,
        generator=generator,
        top_k=10,
    )


def build_result_record(
    case: dict,
    result,
) -> dict:
    return {
        "case_id": case["case_id"],
        "category": case["category"],
        "query": case["query"],
        "expected_behavior": case["expected_behavior"],
        "notes": case.get("notes"),
        "answer": result.answer,
        "citations": [
            {
                "citation_id": citation.citation_id,
                "document_id": citation.document_id,
                "chunk_id": citation.chunk_id,
            }
            for citation in result.citations
        ],
        "sources": [
            {
                "citation_id": source.citation_id,
                "document_id": source.document_id,
                "chunk_id": source.chunk_id,
                "title": source.title,
                "source": source.source,
                "url": source.url,
            }
            for source in result.sources
        ],
        "model": result.model,
        "prompt_tokens": result.prompt_tokens,
        "completion_tokens": result.completion_tokens,
        "total_tokens": result.total_tokens,
        "generation_latency_ms": result.latency_ms,
        "retrieval_latency_ms": result.metadata.get(
            "retrieval_latency_ms"
        ),
        "context_build_latency_ms": result.metadata.get(
            "context_build_latency_ms"
        ),
        "generation_stage_latency_ms": result.metadata.get(
            "generation_stage_latency_ms"
        ),
        "end_to_end_latency_ms": result.metadata.get(
            "end_to_end_latency_ms"
        ),
        "retrieved_results": result.metadata.get(
            "retrieved_results"
        ),
        "context_sources": result.metadata.get(
            "context_sources"
        ),
        "context_tokens": result.metadata.get(
            "context_tokens"
        ),
        "cited_sources": result.metadata.get(
            "cited_sources"
        ),
    }


def main(
    output_path: Path = DEFAULT_OUTPUT_PATH,
) -> None:
    
    output_path.parent.mkdir(
        parents=True,
        exist_ok=True,
    )
    
    cases = load_cases(CASES_PATH)
    
    print()
    print(f"Loaded {len(cases)} generation benchmark cases.")

    pipeline = build_pipeline()

    output_path.parent.mkdir(
        parents=True,
        exist_ok=True,
    )

    # Start a fresh benchmark output.
    output_path.write_text(
        "",
        encoding="utf-8",
    )

    print()
    print("Starting generation benchmark...")
    print()

    benchmark_start = time.perf_counter()

    for index, case in enumerate(cases, start=1):
        query = case["query"]

        print(
            f"[{index:>2}/{len(cases)}] "
            f"{case['case_id']} | "
            f"{case['category']}"
        )

        case_start = time.perf_counter()

        try:
            result = pipeline.run(query)

            record = build_result_record(
                case=case,
                result=result,
            )

            with output_path.open(
                "a",
                encoding="utf-8",
            ) as file:
                file.write(
                    json.dumps(
                        record,
                        ensure_ascii=False,
                    )
                )
                file.write("\n")

            elapsed = time.perf_counter() - case_start

            average = (
                time.perf_counter() - benchmark_start
            ) / index

            remaining = len(cases) - index

            eta_seconds = average * remaining

            print(
                f"     End-to-end: "
                f"{record['end_to_end_latency_ms']:.2f} ms"
            )

            print(
                f"     Tokens: "
                f"{record['prompt_tokens']} + "
                f"{record['completion_tokens']}"
            )

            print(
                f"     Sources: "
                f"{record['context_sources']} context / "
                f"{record['cited_sources']} cited"
            )

            print(
                f"     Case wall time: "
                f"{elapsed:.2f} s | "
                f"ETA: {eta_seconds / 60:.1f} min"
            )

        except Exception as exc:
            error_record = {
                "case_id": case.get("case_id"),
                "category": case.get("category"),
                "query": query,
                "expected_behavior": case.get(
                    "expected_behavior"
                ),
                "error": type(exc).__name__,
                "message": str(exc),
            }

            with output_path.open(
                "a",
                encoding="utf-8",
            ) as file:
                file.write(
                    json.dumps(
                        error_record,
                        ensure_ascii=False,
                    )
                )
                file.write("\n")

            print(
                f"     ERROR: "
                f"{type(exc).__name__}: {exc}"
            )

        print()

    total_seconds = (
        time.perf_counter() - benchmark_start
    )

    print("=" * 60)
    print("GENERATION BENCHMARK COMPLETE")
    print("=" * 60)
    print(f"Cases: {len(cases)}")
    print(f"Total time: {total_seconds / 60:.2f} min")
    print(f"Results: {output_path}")

def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Run generation benchmark v1."
    )

    parser.add_argument(
        "--output",
        type=Path,
        default=DEFAULT_OUTPUT_PATH,
        help=(
            "Path for benchmark JSONL results. "
            "Defaults to the historical results_v3 path."
        ),
    )

    return parser.parse_args()

if __name__ == "__main__":
    args = parse_args()
    main(output_path=args.output)