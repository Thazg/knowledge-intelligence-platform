from pathlib import Path

from backend.chunking.serializer import ChunkSerializer
from backend.embedding.embedder import LocalEmbedder
from backend.vector_store.qdrant_store import (
    QdrantVectorStore,
)


class IndexingPipeline:

    def __init__(
        self,
        input_path: Path,
        collection_name: str,
        model_name: str = "BAAI/bge-small-en-v1.5",
        batch_size: int = 64,
        device: str | None = None,
        qdrant_url: str = "http://localhost:6333",
    ) -> None:

        if batch_size <= 0:
            raise ValueError(
                "batch_size must be greater than 0."
            )

        self.input_path = input_path
        self.batch_size = batch_size

        self.serializer = ChunkSerializer()

        self.embedder = LocalEmbedder(
            model_name=model_name,
            device=device,
        )

        self.vector_store = QdrantVectorStore(
            collection_name=collection_name,
            vector_size=self.embedder.dimension,
            url=qdrant_url,
        )

    def run(
        self,
        limit: int | None = None,
    ) -> int:

        if limit is not None and limit <= 0:
            raise ValueError(
                "limit must be greater than 0."
            )

        self.vector_store.create_collection()

        total_indexed = 0

        for batch in self.serializer.iter_jsonl_batches(
            input_path=self.input_path,
            batch_size=self.batch_size,
        ):

            if limit is not None:
                remaining = limit - total_indexed

                if remaining <= 0:
                    break

                batch = batch[:remaining]

            texts = [
                chunk.content
                for chunk in batch
            ]

            embeddings = self.embedder.embed_documents(
                texts=texts,
                batch_size=self.batch_size,
                show_progress_bar=False,
            )

            indexed_count = (
                self.vector_store.upsert_chunks(
                    chunks=batch,
                    embeddings=embeddings,
                    wait=True,
                )
            )

            total_indexed += indexed_count

            print(
                f"\rIndexed chunks: {total_indexed:,}",
                end="",
                flush=True,
            )

            if (
                limit is not None
                and total_indexed >= limit
            ):
                break

        print()

        return total_indexed