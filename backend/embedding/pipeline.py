from pathlib import Path

import numpy as np
from numpy.typing import NDArray

from backend.chunking.models import Chunk
from backend.chunking.serializer import ChunkSerializer
from backend.embedding.embedder import LocalEmbedder


class EmbeddingPipeline:

    def __init__(
        self,
        input_path: Path,
        model_name: str = "BAAI/bge-small-en-v1.5",
        batch_size: int = 32,
        device: str | None = None,
    ) -> None:

        if batch_size <= 0:
            raise ValueError(
                "batch_size must be greater than 0."
            )

        self.input_path = input_path
        self.batch_size = batch_size

        self.chunk_serializer = ChunkSerializer()

        self.embedder = LocalEmbedder(
            model_name=model_name,
            device=device,
        )

    def run(
        self,
        limit: int | None = None,
        show_progress_bar: bool = True,
    ) -> tuple[list[Chunk], NDArray[np.float32]]:

        chunks = self.chunk_serializer.load_jsonl(
            self.input_path
        )

        if limit is not None:
            if limit <= 0:
                raise ValueError(
                    "limit must be greater than 0."
                )

            chunks = chunks[:limit]

        if not chunks:
            empty_embeddings = np.empty(
                shape=(0, self.embedder.dimension),
                dtype=np.float32,
            )

            return [], empty_embeddings

        embedding_batches: list[
            NDArray[np.float32]
        ] = []

        for start_index in range(
            0,
            len(chunks),
            self.batch_size,
        ):
            end_index = start_index + self.batch_size

            batch_chunks = chunks[
                start_index:end_index
            ]

            batch_texts = [
                chunk.content
                for chunk in batch_chunks
            ]

            batch_embeddings = (
                self.embedder.embed_documents(
                    texts=batch_texts,
                    batch_size=self.batch_size,
                    show_progress_bar=False,
                )
            )

            embedding_batches.append(
                batch_embeddings
            )

            if show_progress_bar:
                processed = min(
                    end_index,
                    len(chunks),
                )

                print(
                    f"\rEmbedded chunks: "
                    f"{processed:,}/{len(chunks):,}",
                    end="",
                    flush=True,
                )

        if show_progress_bar:
            print()

        embeddings = np.concatenate(
            embedding_batches,
            axis=0,
        )

        return chunks, embeddings