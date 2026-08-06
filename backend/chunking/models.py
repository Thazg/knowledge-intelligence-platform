from dataclasses import dataclass


@dataclass
class Chunk:
    chunk_id: str
    document_id: str

    content: str
    chunk_index: int
    token_count: int

    source: str
    filename: str
    relative_path: str

    title: str | None = None