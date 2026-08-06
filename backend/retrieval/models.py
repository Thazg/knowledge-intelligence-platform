from dataclasses import dataclass


@dataclass
class RetrievalResult:
    chunk_id: str
    document_id: str

    content: str
    score: float
    rank: int

    source: str
    filename: str
    relative_path: str
    chunk_index: int
    token_count: int

    title: str | None = None