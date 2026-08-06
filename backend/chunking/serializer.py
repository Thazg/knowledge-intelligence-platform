import json
from pathlib import Path
from collections.abc import Iterator
from backend.chunking.models import Chunk


class ChunkSerializer:

    def save_jsonl(
        self,
        chunks: list[Chunk],
        output_path: Path,
    ) -> None:

        output_path.parent.mkdir(
            parents=True,
            exist_ok=True,
        )

        with output_path.open(
            "w",
            encoding="utf-8",
        ) as file:

            for chunk in chunks:

                record = {
                    "chunk_id": chunk.chunk_id,
                    "document_id": chunk.document_id,
                    "content": chunk.content,
                    "chunk_index": chunk.chunk_index,
                    "token_count": chunk.token_count,
                    "source": chunk.source,
                    "filename": chunk.filename,
                    "relative_path": chunk.relative_path,
                    "title": chunk.title,
                }

                json.dump(
                    record,
                    file,
                    ensure_ascii=False,
                )

                file.write("\n")
    
    def load_jsonl(
        self,
        input_path: Path,
    ) -> list[Chunk]:

        chunks: list[Chunk] = []

        with input_path.open(
            "r",
            encoding="utf-8",
        ) as file:

            for line in file:

                if not line.strip():
                    continue

                record = json.loads(line)

                chunk = Chunk(
                    chunk_id=record["chunk_id"],
                    document_id=record["document_id"],
                    content=record["content"],
                    chunk_index=record["chunk_index"],
                    token_count=record["token_count"],
                    source=record["source"],
                    filename=record["filename"],
                    relative_path=record["relative_path"],
                    title=record.get("title"),
                )

                chunks.append(chunk)

        return chunks
    
    def iter_jsonl_batches(
        self,
        input_path: Path,
        batch_size: int,
    ) -> Iterator[list[Chunk]]:

        if batch_size <= 0:
            raise ValueError(
                "batch_size must be greater than 0."
            )

        batch: list[Chunk] = []

        with input_path.open(
            "r",
            encoding="utf-8",
        ) as file:

            for line in file:

                if not line.strip():
                    continue

                record = json.loads(line)

                chunk = Chunk(
                    chunk_id=record["chunk_id"],
                    document_id=record["document_id"],
                    content=record["content"],
                    chunk_index=record["chunk_index"],
                    token_count=record["token_count"],
                    source=record["source"],
                    filename=record["filename"],
                    relative_path=record["relative_path"],
                    title=record.get("title"),
                )

                batch.append(chunk)

                if len(batch) == batch_size:
                    yield batch
                    batch = []

        if batch:
            yield batch