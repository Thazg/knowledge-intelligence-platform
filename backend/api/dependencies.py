from __future__ import annotations

import logging
import time
from functools import lru_cache

from backend.core.config import Settings, get_settings
from backend.generation.context_builder import ContextBuilder
from backend.generation.providers.ollama_generator import (
    OllamaGenerator,
)
from backend.generation.rag_pipeline import RAGPipeline
from backend.retrieval.hybrid_retriever import (
    HybridRetriever,
)
from backend.services.rag_service import RAGService


logger = logging.getLogger(__name__)

CLOUD_DENSE_VECTOR_NAME = "dense_vector"
CLOUD_BM25_VECTOR_NAME = "rank_bm25_sparse"


def _build_local_retriever(
    settings: Settings,
) -> HybridRetriever:
    # Keep the local-only dependency graph lazy so
    # importing backend.api.dependencies does not
    # load Torch, SentenceTransformers, or rank_bm25.
    from backend.chunking.serializer import (
        ChunkSerializer,
    )
    from backend.embedding.embedder import (
        LocalEmbedder,
    )
    from backend.retrieval.bm25_retriever import (
        BM25Retriever,
    )
    from backend.retrieval.dense_retriever import (
        DenseRetriever,
    )
    from backend.vector_store.qdrant_store import (
        QdrantVectorStore,
    )

    serializer = ChunkSerializer()
    chunks = serializer.load_jsonl(
        settings.chunks_path
    )

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

    return HybridRetriever(
        dense_retriever=dense,
        bm25_retriever=bm25,
        dense_weight=settings.dense_weight,
        bm25_weight=settings.bm25_weight,
        rrf_k=settings.rrf_k,
    )


def _build_cloud_retriever(
    settings: Settings,
) -> HybridRetriever:
    from qdrant_client import QdrantClient

    from backend.retrieval.fastembed_cloud_dense_retriever import (
        FastEmbedCloudDenseRetriever,
    )
    from backend.retrieval.rank_bm25_cloud_retriever import (
        RankBM25CloudRetriever,
    )
    from backend.retrieval.rank_bm25_query_encoder import (
        RankBM25QueryEncoder,
    )

    if settings.qdrant_api_key is None:
        raise ValueError(
            "cloud retrieval requires "
            "QDRANT_API_KEY"
        )

    artifact_path = (
        settings.bm25_query_artifact_path
    )

    if artifact_path is None:
        raise ValueError(
            "cloud retrieval requires "
            "BM25_QUERY_ARTIFACT_PATH"
        )

    if not artifact_path.is_file():
        raise FileNotFoundError(
            "BM25 query artifact not found: "
            f"{artifact_path}"
        )

    client = QdrantClient(
        url=settings.qdrant_url,
        api_key=(
            settings.qdrant_api_key
            .get_secret_value()
        ),
    )

    dense = FastEmbedCloudDenseRetriever(
        client=client,
        collection_name=(
            settings.qdrant_collection
        ),
        vector_name=(
            CLOUD_DENSE_VECTOR_NAME
        ),
        model_name=settings.embedding_model,
    )

    encoder = RankBM25QueryEncoder(
        artifact_path
    )

    bm25 = RankBM25CloudRetriever(
        encoder=encoder,
        client=client,
        collection_name=(
            settings.qdrant_collection
        ),
        vector_name=(
            CLOUD_BM25_VECTOR_NAME
        ),
    )

    return HybridRetriever(
        dense_retriever=dense,
        bm25_retriever=bm25,
        dense_weight=settings.dense_weight,
        bm25_weight=settings.bm25_weight,
        rrf_k=settings.rrf_k,
    )


@lru_cache(maxsize=1)
def get_rag_service() -> RAGService:
    settings = get_settings()

    if settings.rag_profile != "local":
        raise RuntimeError(
            "cloud RAG profile is not "
            "activated until cloud generation "
            "wiring is available"
        )

    start_time = time.perf_counter()

    logger.info(
        "Initializing RAG service"
    )
    logger.info(
        "RAG profile: %s",
        settings.rag_profile,
    )
    logger.info(
        "Qdrant URL: %s",
        settings.qdrant_url,
    )
    logger.info(
        "Ollama URL: %s",
        settings.ollama_url,
    )
    logger.info(
        "Chunks path: %s",
        settings.chunks_path,
    )

    retriever = _build_local_retriever(
        settings
    )

    context_builder = ContextBuilder(
        max_context_tokens=(
            settings.max_context_tokens
        ),
        max_sources=(
            settings.max_context_sources
        ),
    )

    generator = OllamaGenerator(
        model=settings.generation_model,
        base_url=settings.ollama_url,
        timeout_seconds=(
            settings.generation_timeout_seconds
        ),
        max_concurrent_generations=(
            settings.max_concurrent_generations
        ),
    )

    pipeline = RAGPipeline(
        retriever=retriever,
        context_builder=context_builder,
        generator=generator,
        top_k=settings.retrieval_top_k,
    )

    service = RAGService(
        pipeline=pipeline,
    )

    initialization_latency_ms = (
        time.perf_counter()
        - start_time
    ) * 1000

    logger.info(
        "RAG service initialized "
        "successfully "
        "initialization_latency_ms=%.2f",
        initialization_latency_ms,
    )

    return service