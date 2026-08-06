from pathlib import Path

from backend.chunking.fixed_token_chunker import (
    FixedTokenChunker,
)
from backend.chunking.models import Chunk
from backend.chunking.serializer import ChunkSerializer
from backend.ingestion.serializer import DocumentSerializer
from backend.tokenization.tokenizer import DocumentTokenizer


class ChunkingPipeline:

    def __init__(
        self,
        input_path: Path,
        output_path: Path,
        model_name: str = "BAAI/bge-small-en-v1.5",
        chunk_size: int = 384,
        chunk_overlap: int = 64,
    ) -> None:

        self.input_path = input_path
        self.output_path = output_path

        self.document_serializer = DocumentSerializer()
        self.chunk_serializer = ChunkSerializer()

        self.tokenizer = DocumentTokenizer(
            model_name=model_name,
        )

        self.chunker = FixedTokenChunker(
            tokenizer=self.tokenizer,
            chunk_size=chunk_size,
            chunk_overlap=chunk_overlap,
        )

    def run(self) -> list[Chunk]:

        documents = self.document_serializer.load_jsonl(
            self.input_path
        )

        all_chunks: list[Chunk] = []

        for document in documents:
            document_chunks = self.chunker.chunk_document(
                document
            )

            all_chunks.extend(document_chunks)

        self.chunk_serializer.save_jsonl(
            chunks=all_chunks,
            output_path=self.output_path,
        )

        return all_chunks