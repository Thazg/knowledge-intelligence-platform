from __future__ import annotations

from functools import lru_cache

from backend.chunking.serializer import ChunkSerializer
from backend.core.config import get_settings
from backend.embedding.embedder import LocalEmbedder
from backend.generation.context_builder import ContextBuilder
from backend.generation.providers.ollama_generator import OllamaGenerator
from backend.generation.rag_pipeline import RAGPipeline
from backend.retrieval.bm25_retriever import BM25Retriever
from backend.retrieval.dense_retriever import DenseRetriever
from backend.retrieval.hybrid_retriever import HybridRetriever
from backend.services.rag_service import RAGService
from backend.vector_store.qdrant_store import QdrantVectorStore


@lru_cache(maxsize=1)
def get_rag_service() -> RAGService:
    settings = get_settings()

    print("Initializing RAG service...")
    print(f"Qdrant URL: {settings.qdrant_url}")
    print(f"Ollama URL: {settings.ollama_url}")
    print(f"Chunks path: {settings.chunks_path}")

    serializer = ChunkSerializer()
    chunks = serializer.load_jsonl(settings.chunks_path)

    embedder = LocalEmbedder(
        model_name=settings.embedding_model,
    )

    vector_store = QdrantVectorStore(
        collection_name=settings.qdrant_collection,
        vector_size=embedder.dimension,
        url=settings.qdrant_url,
    )

    dense = DenseRetriever(
        embedder=embedder,
        vector_store=vector_store,
    )

    bm25 = BM25Retriever(
        chunks=chunks,
    )

    retriever = HybridRetriever(
        dense_retriever=dense,
        bm25_retriever=bm25,
        dense_weight=settings.dense_weight,
        bm25_weight=settings.bm25_weight,
        rrf_k=settings.rrf_k,
    )

    context_builder = ContextBuilder(
        max_context_tokens=settings.max_context_tokens,
        max_sources=settings.max_context_sources,
    )

    generator = OllamaGenerator(
        model=settings.generation_model,
        base_url=settings.ollama_url,
    )

    pipeline = RAGPipeline(
        retriever=retriever,
        context_builder=context_builder,
        generator=generator,
        top_k=settings.retrieval_top_k,
    )

    return RAGService(
        pipeline=pipeline,
    )