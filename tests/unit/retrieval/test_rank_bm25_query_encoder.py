from __future__ import annotations

import json
from pathlib import Path

import pytest

from backend.retrieval.rank_bm25_query_encoder import (
    RankBM25QueryEncoder,
)


def _write_artifact(
    path: Path,
) -> None:
    artifact = {
        "version": 1,
        "kind": "rank_bm25_query_encoder",
        "corpus": {
            "path": (
                "data/processed/"
                "chunks_fixed.jsonl"
            ),
            "sha256": "abc123",
            "chunks": 3,
        },
        "tokenization": {
            "pattern": (
                r"[a-z0-9]+"
                r"(?:[._/-][a-z0-9]+)*"
            ),
            "lowercase": True,
        },
        "bm25": {
            "implementation": (
                "rank_bm25.BM25Okapi"
            ),
            "k1": 1.5,
            "b": 0.75,
            "epsilon": 0.25,
            "avgdl": 10.0,
        },
        "sparse": {
            "vector_name": (
                "rank_bm25_sparse"
            ),
            "vocabulary_size": 3,
            "term_table_format": (
                "term -> [index, idf]"
            ),
            "terms": {
                "kubernetes": [3, 2.0],
                "deployment": [7, 1.5],
                "docker": [11, 0.5],
            },
        },
    }

    path.write_text(
        json.dumps(artifact),
        encoding="utf-8",
    )


def test_encode_preserves_token_frequency(
    tmp_path: Path,
) -> None:
    artifact_path = (
        tmp_path / "artifact.json"
    )

    _write_artifact(
        artifact_path
    )

    encoder = RankBM25QueryEncoder(
        artifact_path
    )

    vector = encoder.encode(
        "Kubernetes deployment "
        "deployment"
    )

    assert vector is not None
    assert vector.indices == [3, 7]
    assert vector.values == pytest.approx(
        [2.0, 3.0]
    )


def test_tokenize_matches_existing_regex_shape(
    tmp_path: Path,
) -> None:
    artifact_path = (
        tmp_path / "artifact.json"
    )

    _write_artifact(
        artifact_path
    )

    encoder = RankBM25QueryEncoder(
        artifact_path
    )

    assert encoder.tokenize(
        "API/V1 foo_bar abc-def X.Y"
    ) == [
        "api/v1",
        "foo_bar",
        "abc-def",
        "x.y",
    ]


def test_encode_ignores_out_of_vocabulary_terms(
    tmp_path: Path,
) -> None:
    artifact_path = (
        tmp_path / "artifact.json"
    )

    _write_artifact(
        artifact_path
    )

    encoder = RankBM25QueryEncoder(
        artifact_path
    )

    vector = encoder.encode(
        "unknown kubernetes"
    )

    assert vector is not None
    assert vector.indices == [3]
    assert vector.values == pytest.approx(
        [2.0]
    )


def test_encode_returns_none_when_no_terms_match(
    tmp_path: Path,
) -> None:
    artifact_path = (
        tmp_path / "artifact.json"
    )

    _write_artifact(
        artifact_path
    )

    encoder = RankBM25QueryEncoder(
        artifact_path
    )

    assert (
        encoder.encode(
            "unknown terms"
        )
        is None
    )


def test_encode_rejects_empty_query(
    tmp_path: Path,
) -> None:
    artifact_path = (
        tmp_path / "artifact.json"
    )

    _write_artifact(
        artifact_path
    )

    encoder = RankBM25QueryEncoder(
        artifact_path
    )

    with pytest.raises(
        ValueError,
        match="query must not be empty",
    ):
        encoder.encode("   ")


def test_artifact_metadata_is_exposed(
    tmp_path: Path,
) -> None:
    artifact_path = (
        tmp_path / "artifact.json"
    )

    _write_artifact(
        artifact_path
    )

    encoder = RankBM25QueryEncoder(
        artifact_path
    )

    assert (
        encoder.vector_name
        == "rank_bm25_sparse"
    )
    assert (
        encoder.corpus_sha256
        == "abc123"
    )
    assert encoder.corpus_chunks == 3


def test_rejects_wrong_artifact_version(
    tmp_path: Path,
) -> None:
    artifact_path = (
        tmp_path / "artifact.json"
    )

    artifact_path.write_text(
        json.dumps(
            {
                "version": 2,
                "kind": (
                    "rank_bm25_query_encoder"
                ),
            }
        ),
        encoding="utf-8",
    )

    with pytest.raises(
        ValueError,
        match="Unsupported",
    ):
        RankBM25QueryEncoder(
            artifact_path
        )