from dataclasses import asdict

import pytest

from backend.chunking.models import Chunk


CHUNK_FIELDS = {
    "chunk_id": "chunk-001",
    "document_id": "document-001",
    "content": "Docker containers package applications and dependencies.",
    "chunk_index": 0,
    "token_count": 9,
    "source": "docker",
    "filename": "containers.md",
    "relative_path": "docker/guides/containers.md",
    "title": "Docker Containers",
}


def test_chunk_preserves_supplied_fields() -> None:
    chunk = Chunk(**CHUNK_FIELDS)

    assert chunk.chunk_id == "chunk-001"
    assert chunk.document_id == "document-001"
    assert chunk.content == (
        "Docker containers package applications and dependencies."
    )
    assert chunk.chunk_index == 0
    assert chunk.token_count == 9
    assert chunk.source == "docker"
    assert chunk.filename == "containers.md"
    assert chunk.relative_path == "docker/guides/containers.md"
    assert chunk.title == "Docker Containers"


def test_chunk_title_defaults_to_none() -> None:
    fields_without_title = {
        key: value
        for key, value in CHUNK_FIELDS.items()
        if key != "title"
    }

    chunk = Chunk(**fields_without_title)

    assert chunk.title is None


def test_chunk_requires_constructor_fields() -> None:
    with pytest.raises(TypeError):
        Chunk()


def test_chunk_supports_dataclass_serialization() -> None:
    chunk = Chunk(**CHUNK_FIELDS)

    assert asdict(chunk) == CHUNK_FIELDS
