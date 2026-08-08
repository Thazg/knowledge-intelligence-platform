from __future__ import annotations

from functools import lru_cache
from pathlib import Path

from backend.chunking.serializer import ChunkSerializer
from backend.embedding.embedder import LocalEmbedder
from backend.generation.context_builder import ContextBuilder
from backend.generation.providers.ollama_generator import OllamaGenerator
from backend.generation.rag_pipeline import RAGPipeline
from backend.retrieval.bm25_retriever import BM25Retriever
from backend.retrieval.dense_retriever import DenseRetriever
from backend.retrieval.hybrid_retriever import HybridRetriever
from backend.services.rag_service import RAGService
from backend.vector_store.qdrant_store import QdrantVectorStore


CHUNKS_PATH = Path("data/processed/chunks_fixed.jsonl")

QDRANT_COLLECTION = "enterprise_knowledge_fixed_bge_small"
EMBEDDING_MODEL = "BAAI/bge-small-en-v1.5"
GENERATION_MODEL = "qwen3:4b-instruct"


@lru_cache(maxsize=1)
def get_rag_service() -> RAGService:
    print("Initializing RAG service...")

    serializer = ChunkSerializer()
    chunks = serializer.load_jsonl(CHUNKS_PATH)

    embedder = LocalEmbedder(
        model_name=EMBEDDING_MODEL,
    )

    vector_store = QdrantVectorStore(
        collection_name=QDRANT_COLLECTION,
        vector_size=embedder.dimension,
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

    pipeline = RAGPipeline(
        retriever=retriever,
        context_builder=context_builder,
        generator=generator,
        top_k=10,
    )

    return RAGService(
        pipeline=pipeline,
    )