from __future__ import annotations

import argparse
import hashlib
import json
import os
import time
from pathlib import Path
from typing import Any, Iterable

from qdrant_client import QdrantClient, models

from backend.chunking.serializer import ChunkSerializer
from backend.retrieval.bm25_retriever import BM25Retriever


PROJECT_ROOT = Path(__file__).resolve().parents[1]

DEFAULT_CHUNKS_PATH = (
    PROJECT_ROOT
    / "data"
    / "processed"
    / "chunks_fixed.jsonl"
)

DEFAULT_ARTIFACT_PATH = (
    PROJECT_ROOT
    / ".benchmark-results"
    / "rank-bm25-query-artifact-v1.json"
)

DEFAULT_REPORT_PATH = (
    PROJECT_ROOT
    / ".benchmark-results"
    / "qdrant-cloud-bge-rank-bm25-full-migration-v1.json"
)

SOURCE_COLLECTION = (
    "enterprise_knowledge_fixed_bge_small"
)

TARGET_COLLECTION = (
    "enterprise_knowledge_cloud_bge_rank_bm25_v1"
)

DENSE_VECTOR_NAME = "dense_vector"
SPARSE_VECTOR_NAME = "rank_bm25_sparse"

DENSE_SIZE = 384

DEFAULT_LOCAL_QDRANT_URL = "http://localhost:6333"

TOKEN_PATTERN = (
    r"[a-z0-9]+(?:[._/-][a-z0-9]+)*"
)


def _require_env(name: str) -> str:
    value = os.getenv(name, "").strip()

    if not value:
        raise RuntimeError(
            f"{name} is required. "
            "Set it in the current shell before running."
        )

    return value


def _sha256(path: Path) -> str:
    digest = hashlib.sha256()

    with path.open("rb") as handle:
        while True:
            block = handle.read(
                1024 * 1024
            )

            if not block:
                break

            digest.update(block)

    return digest.hexdigest()


def _is_number_sequence(
    value: Any,
) -> bool:
    if not isinstance(
        value,
        (list, tuple),
    ):
        return False

    if not value:
        return False

    return all(
        isinstance(item, (int, float))
        for item in value
    )


def _extract_dense_vector(
    vector: Any,
) -> list[float]:
    if _is_number_sequence(vector):
        dense = [
            float(item)
            for item in vector
        ]

        if len(dense) != DENSE_SIZE:
            raise ValueError(
                "Unexpected dense vector size: "
                f"{len(dense)}"
            )

        return dense

    if isinstance(vector, dict):
        candidates = []

        for name, value in vector.items():
            if not _is_number_sequence(value):
                continue

            dense = [
                float(item)
                for item in value
            ]

            if len(dense) == DENSE_SIZE:
                candidates.append(
                    (str(name), dense)
                )

        if len(candidates) == 1:
            return candidates[0][1]

        if not candidates:
            raise ValueError(
                "No 384-dimensional dense "
                "vector found in source point."
            )

        raise ValueError(
            "Multiple 384-dimensional dense "
            "vectors found in source point: "
            f"{[name for name, _ in candidates]}"
        )

    raise TypeError(
        "Unsupported source vector type: "
        f"{type(vector).__name__}"
    )


def _build_vocabulary(
    bm25: BM25Retriever,
) -> dict[str, int]:
    terms = sorted(
        {
            term
            for frequencies
            in bm25.index.doc_freqs
            for term in frequencies
        }
    )

    return {
        term: index
        for index, term in enumerate(
            terms,
            start=1,
        )
    }


def _encode_document(
    *,
    bm25: BM25Retriever,
    doc_position: int,
    vocabulary: dict[str, int],
) -> models.SparseVector:
    index = bm25.index

    frequencies = index.doc_freqs[
        doc_position
    ]

    doc_length = index.doc_len[
        doc_position
    ]

    normalization = (
        index.k1
        * (
            1
            - index.b
            + (
                index.b
                * doc_length
                / index.avgdl
            )
        )
    )

    entries = []

    for term, frequency in (
        frequencies.items()
    ):
        value = (
            frequency
            * (index.k1 + 1)
            / (
                frequency
                + normalization
            )
        )

        if value == 0:
            continue

        entries.append(
            (
                vocabulary[term],
                float(value),
            )
        )

    entries.sort(
        key=lambda item: item[0]
    )

    return models.SparseVector(
        indices=[
            index
            for index, _ in entries
        ],
        values=[
            value
            for _, value in entries
        ],
    )


def _query_artifact(
    *,
    bm25: BM25Retriever,
    vocabulary: dict[str, int],
    chunks_path: Path,
) -> dict[str, Any]:
    term_table = {
        term: [
            vocabulary[term],
            float(idf),
        ]
        for term, idf in bm25.index.idf.items()
    }

    return {
        "version": 1,
        "kind": "rank_bm25_query_encoder",
        "corpus": {
            "path": str(
                chunks_path.relative_to(
                    PROJECT_ROOT
                )
            ).replace("\\", "/"),
            "sha256": _sha256(
                chunks_path
            ),
            "chunks": len(
                bm25.chunks
            ),
        },
        "tokenization": {
            "pattern": TOKEN_PATTERN,
            "lowercase": True,
        },
        "bm25": {
            "implementation": (
                "rank_bm25.BM25Okapi"
            ),
            "k1": float(
                bm25.index.k1
            ),
            "b": float(
                bm25.index.b
            ),
            "epsilon": float(
                bm25.index.epsilon
            ),
            "avgdl": float(
                bm25.index.avgdl
            ),
        },
        "sparse": {
            "vector_name": (
                SPARSE_VECTOR_NAME
            ),
            "vocabulary_size": (
                len(vocabulary)
            ),
            "term_table_format": (
                "term -> [index, idf]"
            ),
            "terms": term_table,
        },
    }


def _create_target_collection(
    client: QdrantClient,
    *,
    recreate: bool,
) -> None:
    exists = client.collection_exists(
        TARGET_COLLECTION
    )

    if exists and not recreate:
        raise RuntimeError(
            f"Target collection "
            f"{TARGET_COLLECTION!r} already exists. "
            "Use --recreate only if you intend "
            "to replace this deployment candidate."
        )

    if exists:
        print(
            "Deleting existing target collection..."
        )

        client.delete_collection(
            TARGET_COLLECTION
        )

    print(
        "Creating target collection..."
    )

    client.create_collection(
        collection_name=TARGET_COLLECTION,
        vectors_config={
            DENSE_VECTOR_NAME: (
                models.VectorParams(
                    size=DENSE_SIZE,
                    distance=(
                        models.Distance.COSINE
                    ),
                )
            ),
        },
        sparse_vectors_config={
            SPARSE_VECTOR_NAME: (
                models.SparseVectorParams(
                    index=(
                        models.SparseIndexParams()
                    )
                )
            )
        },
    )


def _iter_source_pages(
    client: QdrantClient,
    *,
    page_size: int,
) -> Iterable[list[Any]]:
    offset = None

    while True:
        records, next_offset = client.scroll(
            collection_name=SOURCE_COLLECTION,
            limit=page_size,
            offset=offset,
            with_payload=True,
            with_vectors=True,
        )

        if not records:
            return

        yield records

        if next_offset is None:
            return

        offset = next_offset


def _canonical_payload(
    payload: dict[str, Any] | None,
) -> dict[str, Any]:
    source = dict(payload or {})

    canonical = {
        "chunk_id": str(
            source.get("chunk_id", "")
        ),
        "document_id": str(
            source.get("document_id", "")
        ),
        "content": str(
            source.get("content", "")
        ),
        "chunk_index": int(
            source.get("chunk_index", 0)
        ),
        "token_count": int(
            source.get("token_count", 0)
        ),
        "source": str(
            source.get("source", "")
        ),
        "filename": str(
            source.get("filename", "")
        ),
        "relative_path": str(
            source.get("relative_path", "")
        ),
        "title": source.get("title"),
    }

    if not canonical["chunk_id"]:
        raise ValueError(
            "Source point is missing chunk_id."
        )

    if not canonical["content"].strip():
        raise ValueError(
            "Source point is missing content."
        )

    return canonical


def _build_target_point(
    *,
    record: Any,
    bm25: BM25Retriever,
    vocabulary: dict[str, int],
    chunk_positions: dict[str, int],
) -> models.PointStruct:
    payload = _canonical_payload(
        record.payload
    )

    chunk_id = payload["chunk_id"]

    try:
        doc_position = (
            chunk_positions[
                chunk_id
            ]
        )
    except KeyError as exc:
        raise RuntimeError(
            "Local Qdrant point chunk_id "
            "was not found in chunks_fixed.jsonl: "
            f"{chunk_id}"
        ) from exc

    dense_vector = (
        _extract_dense_vector(
            record.vector
        )
    )

    sparse_vector = _encode_document(
        bm25=bm25,
        doc_position=doc_position,
        vocabulary=vocabulary,
    )

    return models.PointStruct(
        id=record.id,
        vector={
            DENSE_VECTOR_NAME: (
                dense_vector
            ),
            SPARSE_VECTOR_NAME: (
                sparse_vector
            ),
        },
        payload=payload,
    )


def _parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description=(
            "Build the full rank_bm25 query "
            "artifact and migrate canonical BGE "
            "dense vectors plus exact "
            "rank_bm25-compatible sparse vectors "
            "to Qdrant Cloud."
        )
    )

    parser.add_argument(
        "--chunks",
        type=Path,
        default=DEFAULT_CHUNKS_PATH,
    )

    parser.add_argument(
        "--local-qdrant-url",
        default=DEFAULT_LOCAL_QDRANT_URL,
    )

    parser.add_argument(
        "--page-size",
        type=int,
        default=64,
    )

    parser.add_argument(
        "--batch-size",
        type=int,
        default=64,
    )

    parser.add_argument(
        "--artifact-output",
        type=Path,
        default=DEFAULT_ARTIFACT_PATH,
    )

    parser.add_argument(
        "--report-output",
        type=Path,
        default=DEFAULT_REPORT_PATH,
    )

    parser.add_argument(
        "--recreate",
        action="store_true",
    )

    args = parser.parse_args()

    if args.page_size < 1:
        parser.error(
            "--page-size must be >= 1"
        )

    if args.batch_size < 1:
        parser.error(
            "--batch-size must be >= 1"
        )

    return args


def main() -> None:
    args = _parse_args()

    cloud_url = _require_env(
        "QDRANT_URL"
    )

    cloud_api_key = _require_env(
        "QDRANT_API_KEY"
    )

    print(
        "FULL BGE + EXACT RANK_BM25 MIGRATION"
    )
    print(
        "===================================="
    )
    print(
        f"Chunks: {args.chunks}"
    )
    print(
        f"Source collection: "
        f"{SOURCE_COLLECTION}"
    )
    print(
        f"Target collection: "
        f"{TARGET_COLLECTION}"
    )
    print()

    serializer = ChunkSerializer()

    print(
        "Loading canonical chunks..."
    )

    chunks = serializer.load_jsonl(
        args.chunks
    )

    print(
        f"Loaded chunks: {len(chunks):,}"
    )

    chunk_positions = {}

    for position, chunk in enumerate(
        chunks
    ):
        if chunk.chunk_id in chunk_positions:
            raise RuntimeError(
                "Duplicate chunk_id in corpus: "
                f"{chunk.chunk_id}"
            )

        chunk_positions[
            chunk.chunk_id
        ] = position

    print(
        "Building full canonical "
        "BM25Okapi offline..."
    )

    build_started = time.perf_counter()

    bm25 = BM25Retriever(
        chunks=chunks
    )

    bm25_build_seconds = (
        time.perf_counter()
        - build_started
    )

    print(
        "BM25 build completed in "
        f"{bm25_build_seconds:.2f}s"
    )

    print(
        "Building deterministic vocabulary..."
    )

    vocabulary = _build_vocabulary(
        bm25
    )

    print(
        f"Vocabulary size: "
        f"{len(vocabulary):,}"
    )

    artifact = _query_artifact(
        bm25=bm25,
        vocabulary=vocabulary,
        chunks_path=args.chunks,
    )

    args.artifact_output.parent.mkdir(
        parents=True,
        exist_ok=True,
    )

    args.artifact_output.write_text(
        json.dumps(
            artifact,
            ensure_ascii=False,
            separators=(",", ":"),
        )
        + "\n",
        encoding="utf-8",
    )

    artifact_size_mb = (
        args.artifact_output.stat().st_size
        / (1024 * 1024)
    )

    print(
        "Query artifact written to: "
        f"{args.artifact_output}"
    )
    print(
        "Query artifact size: "
        f"{artifact_size_mb:.2f} MB"
    )

    local_client = QdrantClient(
        url=args.local_qdrant_url,
        timeout=30.0,
    )

    if not local_client.collection_exists(
        SOURCE_COLLECTION
    ):
        raise RuntimeError(
            "Canonical local BGE collection "
            "does not exist."
        )

    source_count = int(
        local_client.count(
            collection_name=SOURCE_COLLECTION,
            exact=True,
        ).count
    )

    if source_count != len(chunks):
        raise RuntimeError(
            "Source collection / corpus count "
            "mismatch: "
            f"collection={source_count} "
            f"chunks={len(chunks)}"
        )

    cloud_client = QdrantClient(
        url=cloud_url,
        api_key=cloud_api_key,
        timeout=120.0,
    )

    _create_target_collection(
        cloud_client,
        recreate=args.recreate,
    )

    print()
    print(
        "Migrating canonical dense + "
        "exact sparse vectors..."
    )

    migration_started = (
        time.perf_counter()
    )

    migrated = 0

    for page_number, records in enumerate(
        _iter_source_pages(
            local_client,
            page_size=args.page_size,
        ),
        start=1,
    ):
        points = [
            _build_target_point(
                record=record,
                bm25=bm25,
                vocabulary=vocabulary,
                chunk_positions=(
                    chunk_positions
                ),
            )
            for record in records
        ]

        cloud_client.upload_points(
            collection_name=(
                TARGET_COLLECTION
            ),
            points=points,
            batch_size=args.batch_size,
            parallel=1,
            max_retries=3,
            wait=True,
        )

        migrated += len(points)

        print(
            f"Page {page_number:04d}: "
            f"migrated={migrated:,}/"
            f"{source_count:,}"
        )

    migration_seconds = (
        time.perf_counter()
        - migration_started
    )

    actual_count = int(
        cloud_client.count(
            collection_name=(
                TARGET_COLLECTION
            ),
            exact=True,
        ).count
    )

    print()
    print(
        "Migration completed in "
        f"{migration_seconds:.2f}s"
    )
    print(
        "Exact target points: "
        f"{actual_count:,}"
    )

    if migrated != source_count:
        raise RuntimeError(
            "Migrated point count mismatch: "
            f"expected={source_count} "
            f"migrated={migrated}"
        )

    if actual_count != source_count:
        raise RuntimeError(
            "Target collection count mismatch: "
            f"expected={source_count} "
            f"actual={actual_count}"
        )

    report = {
        "status": "pass",
        "source_collection": (
            SOURCE_COLLECTION
        ),
        "target_collection": (
            TARGET_COLLECTION
        ),
        "points": actual_count,
        "chunks_sha256": (
            artifact["corpus"]["sha256"]
        ),
        "dense": {
            "source": (
                "canonical_local_bge_vector"
            ),
            "dimension": DENSE_SIZE,
            "reembedded": False,
        },
        "sparse": {
            "source": (
                "rank_bm25.BM25Okapi"
            ),
            "vector_name": (
                SPARSE_VECTOR_NAME
            ),
            "vocabulary_size": (
                len(vocabulary)
            ),
            "k1": bm25.index.k1,
            "b": bm25.index.b,
            "epsilon": bm25.index.epsilon,
            "avgdl": bm25.index.avgdl,
        },
        "artifact": {
            "path": str(
                args.artifact_output
            ),
            "size_mb": (
                artifact_size_mb
            ),
        },
        "timing": {
            "bm25_build_seconds": (
                bm25_build_seconds
            ),
            "migration_seconds": (
                migration_seconds
            ),
        },
    }

    args.report_output.parent.mkdir(
        parents=True,
        exist_ok=True,
    )

    args.report_output.write_text(
        json.dumps(
            report,
            indent=2,
            ensure_ascii=False,
        )
        + "\n",
        encoding="utf-8",
    )

    print(
        "Report written to: "
        f"{args.report_output}"
    )
    print()
    print(
        "FULL MIGRATION PASS: "
        "canonical BGE dense vectors and "
        "rank_bm25-compatible sparse vectors "
        "are now stored in Qdrant Cloud."
    )


if __name__ == "__main__":
    main()