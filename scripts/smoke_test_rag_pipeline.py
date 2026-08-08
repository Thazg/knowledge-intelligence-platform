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


CHUNKS_PATH = Path("data/processed/chunks_fixed.jsonl")
QDRANT_COLLECTION = "enterprise_knowledge_fixed_bge_small"
EMBEDDING_MODEL = "BAAI/bge-small-en-v1.5"


def main() -> None:
    print("Loading chunks...")
    serializer = ChunkSerializer()
    chunks = serializer.load_jsonl(CHUNKS_PATH)

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
        model="qwen3:4b-instruct",
    )

    pipeline = RAGPipeline(
        retriever=weighted_rrf,
        context_builder=context_builder,
        generator=generator,
        top_k=10,
    )

    query = (
        "How do I deploy a FastAPI application "
        "on Kubernetes?"
    )

    print()
    print("QUERY")
    print("-----")
    print(query)

    print()
    print("Running RAG pipeline...")

    result = pipeline.run(query)

    print()
    print("ANSWER")
    print("------")
    print(result.answer)

    print()
    print("CITATIONS")
    print("---------")
    for citation in result.citations:
        print(citation)

    print()
    print("SOURCES")
    print("-------")
    for source in result.sources:
        print(
            f"[{source.citation_id}] "
            f"{source.title} | "
            f"{source.source} | "
            f"{source.chunk_id}"
        )

    print()
    print("TOKENS")
    print("------")
    print("Prompt:", result.prompt_tokens)
    print("Completion:", result.completion_tokens)
    print("Total:", result.total_tokens)

    print()
    print("GENERATION LATENCY")
    print("------------------")
    print(f"{result.latency_ms:.2f} ms")

    print()
    print("PIPELINE TIMINGS")
    print("----------------")

    print(
        "Retrieval:",
        f"{result.metadata['retrieval_latency_ms']:.2f} ms",
    )

    print(
        "Context build:",
        f"{result.metadata['context_build_latency_ms']:.2f} ms",
    )

    print(
        "Generation stage:",
        f"{result.metadata['generation_stage_latency_ms']:.2f} ms",
    )

    print(
        "End-to-end:",
        f"{result.metadata['end_to_end_latency_ms']:.2f} ms",
    )

    print()
    print("PIPELINE COUNTS")
    print("---------------")
    print(
        "Retrieved results:",
        result.metadata["retrieved_results"],
    )
    print(
        "Context sources:",
        result.metadata["context_sources"],
    )
    print(
        "Context tokens:",
        result.metadata["context_tokens"],
    )
    print(
        "Cited sources:",
        result.metadata["cited_sources"],
    )

if __name__ == "__main__":
    main()