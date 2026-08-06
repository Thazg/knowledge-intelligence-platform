from dataclasses import dataclass, field
from pathlib import Path


@dataclass(slots=True)
class DocumentFile:
    """
    Represents a discovered document on disk.
    """

    # Dataset
    source: str

    # Absolute path
    path: Path

    # Relative path inside the dataset
    relative_path: Path

    # overview.mdx
    filename: str

    # .mdx
    extension: str

    # File size in bytes
    size_bytes: int


@dataclass(slots=True)
class Document:
    """
    Parsed document.
    """

    document_id: str

    content: str

    source: str

    filename: str

    relative_path: Path

    extension: str

    title: str = ""

    headings: list[str] = field(default_factory=list)

    word_count: int = 0

    token_count: int = 0
