from __future__ import annotations

import argparse
import json
import re
from collections import defaultdict
from dataclasses import asdict, dataclass
from pathlib import Path
from typing import Any

from backend.chunking.serializer import ChunkSerializer
from backend.embedding.embedder import LocalEmbedder
from backend.retrieval.bm25_retriever import BM25Retriever
from backend.retrieval.dense_retriever import DenseRetriever
from backend.vector_store.qdrant_store import QdrantVectorStore


# ---------------------------------------------------------------------------
# Project paths
# ---------------------------------------------------------------------------

PROJECT_ROOT = Path(__file__).resolve().parents[1]

DEFAULT_PLAN_PATH = (
    PROJECT_ROOT
    / "benchmarks"
    / "retrieval"
    / "case_plan.md"
)

DEFAULT_CHUNKS_PATH = (
    PROJECT_ROOT
    / "data"
    / "processed"
    / "chunks_fixed.jsonl"
)

DEFAULT_OUTPUT_PATH = (
    PROJECT_ROOT
    / "benchmarks"
    / "retrieval"
    / "candidates.jsonl"
)

DEFAULT_REVIEW_DIR = (
    PROJECT_ROOT
    / "benchmarks"
    / "retrieval"
    / "review"
)

DEFAULT_NORMALIZED_PLAN_PATH = (
    PROJECT_ROOT
    / "benchmarks"
    / "retrieval"
    / "planned_cases.jsonl"
)


COLLECTION_NAME = "enterprise_knowledge_fixed_bge_small"
EMBEDDING_MODEL = "BAAI/bge-small-en-v1.5"


# ---------------------------------------------------------------------------
# Models
# ---------------------------------------------------------------------------


@dataclass(frozen=True)
class PlannedCase:
    case_id: str
    query: str
    category: str
    source_hint: str | None
    state: str


@dataclass
class CandidateDocument:
    source: str
    path: str

    title: str | None

    dense_rank: int | None
    bm25_rank: int | None

    dense_score: float | None
    bm25_score: float | None

    rrf_score: float

    excerpt: str


# ---------------------------------------------------------------------------
# Markdown plan parser
# ---------------------------------------------------------------------------


CATEGORY_HEADINGS = {
    "semantic": "semantic",
    "lexical": "lexical",
    "ambiguous": "ambiguous",
    "version-specific": "version_specific",
    "version specific": "version_specific",
    "cross-tool": "cross_tool",
    "cross tool": "cross_tool",
}


def normalize_markdown_cell(value: str) -> str:
    value = value.strip()

    # Remove inline markdown backticks.
    value = value.replace("`", "")

    # Remove common state decoration.
    value = value.replace("✅", "").strip()

    return value


def detect_category(line: str) -> str | None:
    """
    Detect headings such as:

        # 8. Semantic Cases — 20
        # 9. Lexical Cases — 20
        # 10. Ambiguous Cases — 20
        # 11. Version-Specific Cases — 20
        # 12. Cross-Tool Cases — 20
    """
    stripped = line.strip()

    if not stripped.startswith("#"):
        return None

    lowered = stripped.lower()

    for heading, category in CATEGORY_HEADINGS.items():
        if heading in lowered and "case" in lowered:
            return category

    return None


def parse_markdown_table_row(
    line: str,
) -> list[str] | None:
    """
    Parse:

        | id | query | source | state |

    into a list of cells.
    """
    stripped = line.strip()

    if not stripped.startswith("|"):
        return None

    cells = [
        normalize_markdown_cell(cell)
        for cell in stripped.strip("|").split("|")
    ]

    return cells


def is_separator_row(cells: list[str]) -> bool:
    return all(
        re.fullmatch(r":?-{3,}:?", cell.strip()) is not None
        for cell in cells
    )


def parse_case_plan(path: Path) -> list[PlannedCase]:
    if not path.exists():
        raise FileNotFoundError(
            f"Benchmark plan not found: {path}"
        )

    cases: list[PlannedCase] = []

    current_category: str | None = None
    headers: list[str] | None = None

    with path.open(
        "r",
        encoding="utf-8",
    ) as file:
        for raw_line in file:
            line = raw_line.rstrip("\n")

            detected_category = detect_category(line)

            if detected_category is not None:
                current_category = detected_category
                headers = None
                continue

            if current_category is None:
                continue

            cells = parse_markdown_table_row(line)

            if not cells:
                continue

            if is_separator_row(cells):
                continue

            lowered = [
                cell.lower()
                for cell in cells
            ]

            # Table header
            if "id" in lowered and "query" in lowered:
                headers = lowered
                continue

            if headers is None:
                continue

            if len(cells) != len(headers):
                continue

            row = dict(zip(headers, cells))

            case_id = row.get("id")
            query = row.get("query")

            if not case_id or not query:
                continue

            source_hint = (
                row.get("primary source")
                or row.get("source")
                or row.get("relevant sources")
            )

            state = (
                row.get("state")
                or "planned"
            )

            cases.append(
                PlannedCase(
                    case_id=case_id,
                    query=query,
                    category=current_category,
                    source_hint=source_hint,
                    state=state.lower(),
                )
            )

    if not cases:
        raise RuntimeError(
            "No benchmark cases were parsed from case_plan.md."
        )

    return cases


# ---------------------------------------------------------------------------
# Generic RetrievalResult helpers
# ---------------------------------------------------------------------------


def get_attr(
    result: Any,
    *names: str,
    default: Any = None,
) -> Any:
    """
    Makes this script tolerant of minor naming differences in
    RetrievalResult.
    """
    for name in names:
        if hasattr(result, name):
            value = getattr(result, name)

            if value is not None:
                return value

    return default


def result_source(result: Any) -> str:
    return str(
        get_attr(
            result,
            "source",
            default="unknown",
        )
    )


def result_path(result: Any) -> str:
    return str(
        get_attr(
            result,
            "relative_path",
            "path",
            default="unknown",
        )
    )


def result_content(result: Any) -> str:
    return str(
        get_attr(
            result,
            "content",
            "text",
            default="",
        )
    )


def result_title(result: Any) -> str | None:
    value = get_attr(
        result,
        "title",
        default=None,
    )

    if value is None:
        return None

    return str(value)


def result_score(result: Any) -> float | None:
    value = get_attr(
        result,
        "score",
        default=None,
    )

    if value is None:
        return None

    try:
        return float(value)
    except (TypeError, ValueError):
        return None


# ---------------------------------------------------------------------------
# Text helpers
# ---------------------------------------------------------------------------


def normalize_whitespace(text: str) -> str:
    return re.sub(
        r"\s+",
        " ",
        text,
    ).strip()


def make_excerpt(
    text: str,
    max_chars: int = 700,
) -> str:
    """
    Keep review files readable.

    We intentionally do not dump the entire chunk/document.
    """
    text = normalize_whitespace(text)

    if len(text) <= max_chars:
        return text

    return text[:max_chars].rstrip() + "..."


# ---------------------------------------------------------------------------
# Candidate fusion
# ---------------------------------------------------------------------------


def build_rank_map(
    results: list[Any],
) -> dict[tuple[str, str], tuple[int, Any]]:
    """
    Document-level dedup.

    If multiple chunks from the same document are retrieved,
    preserve only the best-ranked chunk.
    """
    output: dict[
        tuple[str, str],
        tuple[int, Any],
    ] = {}

    for rank, result in enumerate(
        results,
        start=1,
    ):
        key = (
            result_source(result),
            result_path(result),
        )

        if key not in output:
            output[key] = (
                rank,
                result,
            )

    return output


def fuse_candidates(
    dense_results: list[Any],
    bm25_results: list[Any],
    *,
    rrf_k: int = 60,
    top_documents: int = 10,
) -> list[CandidateDocument]:
    dense_map = build_rank_map(
        dense_results
    )

    bm25_map = build_rank_map(
        bm25_results
    )

    all_documents = (
        set(dense_map)
        | set(bm25_map)
    )

    candidates: list[
        CandidateDocument
    ] = []

    for key in all_documents:
        dense_item = dense_map.get(key)
        bm25_item = bm25_map.get(key)

        dense_rank = (
            dense_item[0]
            if dense_item
            else None
        )

        bm25_rank = (
            bm25_item[0]
            if bm25_item
            else None
        )

        rrf_score = 0.0

        if dense_rank is not None:
            rrf_score += (
                1.0
                / (rrf_k + dense_rank)
            )

        if bm25_rank is not None:
            rrf_score += (
                1.0
                / (rrf_k + bm25_rank)
            )

        # Prefer dense chunk for excerpt if present.
        # Otherwise fall back to BM25.
        selected_result = (
            dense_item[1]
            if dense_item
            else bm25_item[1]
        )

        source, path = key

        candidates.append(
            CandidateDocument(
                source=source,
                path=path,
                title=result_title(
                    selected_result
                ),
                dense_rank=dense_rank,
                bm25_rank=bm25_rank,
                dense_score=(
                    result_score(
                        dense_item[1]
                    )
                    if dense_item
                    else None
                ),
                bm25_score=(
                    result_score(
                        bm25_item[1]
                    )
                    if bm25_item
                    else None
                ),
                rrf_score=rrf_score,
                excerpt=make_excerpt(
                    result_content(
                        selected_result
                    )
                ),
            )
        )

    candidates.sort(
        key=lambda item: item.rrf_score,
        reverse=True,
    )

    return candidates[:top_documents]


# ---------------------------------------------------------------------------
# Output
# ---------------------------------------------------------------------------


def write_normalized_plan(
    cases: list[PlannedCase],
    path: Path,
) -> None:
    path.parent.mkdir(
        parents=True,
        exist_ok=True,
    )

    with path.open(
        "w",
        encoding="utf-8",
    ) as file:
        for case in cases:
            file.write(
                json.dumps(
                    asdict(case),
                    ensure_ascii=False,
                )
                + "\n"
            )


def write_candidates_jsonl(
    records: list[dict[str, Any]],
    path: Path,
) -> None:
    path.parent.mkdir(
        parents=True,
        exist_ok=True,
    )

    with path.open(
        "w",
        encoding="utf-8",
    ) as file:
        for record in records:
            file.write(
                json.dumps(
                    record,
                    ensure_ascii=False,
                )
                + "\n"
            )


def write_review_markdown(
    records: list[dict[str, Any]],
    output_dir: Path,
) -> None:
    output_dir.mkdir(
        parents=True,
        exist_ok=True,
    )

    grouped: dict[
        str,
        list[dict[str, Any]],
    ] = defaultdict(list)

    for record in records:
        grouped[
            record["category"]
        ].append(record)

    for category, category_records in grouped.items():
        output_path = (
            output_dir
            / f"{category}_candidates.md"
        )

        with output_path.open(
            "w",
            encoding="utf-8",
        ) as file:
            file.write(
                f"# {category.replace('_', ' ').title()} "
                "Ground-Truth Candidates\n\n"
            )

            file.write(
                "> These documents are retrieval candidates only. "
                "They are not ground truth until manually reviewed.\n\n"
            )

            for record in category_records:
                file.write(
                    f"## {record['case_id']}\n\n"
                )

                file.write(
                    f"**Query:** {record['query']}\n\n"
                )

                file.write(
                    f"**Source hint:** "
                    f"{record.get('source_hint') or 'None'}\n\n"
                )

                for index, candidate in enumerate(
                    record["candidates"],
                    start=1,
                ):
                    file.write(
                        f"### Candidate {index}\n\n"
                    )

                    file.write(
                        f"- Source: `{candidate['source']}`\n"
                    )

                    file.write(
                        f"- Path: `{candidate['path']}`\n"
                    )

                    if candidate.get("title"):
                        file.write(
                            f"- Title: {candidate['title']}\n"
                        )

                    file.write(
                        f"- Dense rank: "
                        f"{candidate['dense_rank']}\n"
                    )

                    file.write(
                        f"- BM25 rank: "
                        f"{candidate['bm25_rank']}\n"
                    )

                    file.write(
                        f"- RRF score: "
                        f"{candidate['rrf_score']:.8f}\n\n"
                    )

                    file.write(
                        "**Excerpt:**\n\n"
                    )

                    file.write(
                        candidate["excerpt"]
                        + "\n\n"
                    )

                    file.write("---\n\n")


# ---------------------------------------------------------------------------
# Retriever construction
# ---------------------------------------------------------------------------


def build_retrievers(
    chunks_path: Path,
) -> tuple[
    DenseRetriever,
    BM25Retriever,
]:
    print(
        f"Loading chunks from: {chunks_path}"
    )

    serializer = ChunkSerializer()

    chunks = serializer.load_jsonl(
        chunks_path
    )

    print(
        f"Loaded chunks: {len(chunks):,}"
    )

    print(
        f"Loading embedding model: "
        f"{EMBEDDING_MODEL}"
    )

    embedder = LocalEmbedder(
        model_name=EMBEDDING_MODEL
    )

    print(
        f"Connecting to Qdrant collection: "
        f"{COLLECTION_NAME}"
    )

    vector_store = QdrantVectorStore(
        collection_name=COLLECTION_NAME,
        vector_size=embedder.dimension,
    )

    dense_retriever = DenseRetriever(
        embedder=embedder,
        vector_store=vector_store,
    )

    bm25_retriever = BM25Retriever(
        chunks=chunks
    )

    return (
        dense_retriever,
        bm25_retriever,
    )


# ---------------------------------------------------------------------------
# Main candidate generation
# ---------------------------------------------------------------------------


def generate_candidates(
    cases: list[PlannedCase],
    dense_retriever: DenseRetriever,
    bm25_retriever: BM25Retriever,
    *,
    retrieval_top_k: int,
    candidate_documents: int,
) -> list[dict[str, Any]]:
    records: list[
        dict[str, Any]
    ] = []

    total = len(cases)

    for index, case in enumerate(
        cases,
        start=1,
    ):
        print(
            f"[{index:03d}/{total:03d}] "
            f"{case.case_id}"
        )

        dense_results = (
            dense_retriever.retrieve(
                case.query,
                top_k=retrieval_top_k,
                max_chunks_per_document=None,
                candidate_multiplier=5,
            )
        )

        bm25_results = (
            bm25_retriever.retrieve(
                case.query,
                top_k=retrieval_top_k,
                max_chunks_per_document=None,
                candidate_multiplier=5,
            )
        )

        candidates = fuse_candidates(
            dense_results,
            bm25_results,
            top_documents=candidate_documents,
        )

        records.append(
            {
                "case_id": case.case_id,
                "query": case.query,
                "category": case.category,
                "source_hint": case.source_hint,
                "state": case.state,
                "candidates": [
                    asdict(candidate)
                    for candidate in candidates
                ],
            }
        )

    return records


# ---------------------------------------------------------------------------
# CLI
# ---------------------------------------------------------------------------


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description=(
            "Generate candidate documents for "
            "retrieval benchmark ground-truth review."
        )
    )

    parser.add_argument(
        "--plan",
        type=Path,
        default=DEFAULT_PLAN_PATH,
    )

    parser.add_argument(
        "--chunks",
        type=Path,
        default=DEFAULT_CHUNKS_PATH,
    )

    parser.add_argument(
        "--output",
        type=Path,
        default=DEFAULT_OUTPUT_PATH,
    )

    parser.add_argument(
        "--review-dir",
        type=Path,
        default=DEFAULT_REVIEW_DIR,
    )

    parser.add_argument(
        "--retrieval-top-k",
        type=int,
        default=30,
        help=(
            "Number of chunk-level candidates "
            "retrieved from each retriever."
        ),
    )

    parser.add_argument(
        "--candidate-docs",
        type=int,
        default=10,
        help=(
            "Final document-level candidates "
            "kept per benchmark case."
        ),
    )

    parser.add_argument(
        "--category",
        choices=[
            "semantic",
            "lexical",
            "ambiguous",
            "version_specific",
            "cross_tool",
        ],
        default=None,
        help=(
            "Generate candidates only for one category."
        ),
    )

    parser.add_argument(
        "--include-active",
        action="store_true",
        help=(
            "Also regenerate candidates for cases "
            "already marked active."
        ),
    )

    return parser.parse_args()


def main() -> None:
    args = parse_args()

    print("=" * 72)
    print("BENCHMARK GROUND-TRUTH CANDIDATE GENERATOR")
    print("=" * 72)

    cases = parse_case_plan(
        args.plan
    )

    print(
        f"Cases parsed from plan: {len(cases)}"
    )

    write_normalized_plan(
        cases,
        DEFAULT_NORMALIZED_PLAN_PATH,
    )

    print(
        "Normalized plan written to:"
    )
    print(
        f"  {DEFAULT_NORMALIZED_PLAN_PATH}"
    )

    if args.category:
        cases = [
            case
            for case in cases
            if case.category == args.category
        ]

    if not args.include_active:
        cases = [
            case
            for case in cases
            if "active" not in case.state
        ]

    if not cases:
        print(
            "No benchmark cases selected."
        )
        return

    print(
        f"Cases selected: {len(cases)}"
    )

    dense_retriever, bm25_retriever = (
        build_retrievers(
            args.chunks
        )
    )

    records = generate_candidates(
        cases=cases,
        dense_retriever=dense_retriever,
        bm25_retriever=bm25_retriever,
        retrieval_top_k=args.retrieval_top_k,
        candidate_documents=args.candidate_docs,
    )

    write_candidates_jsonl(
        records,
        args.output,
    )

    write_review_markdown(
        records,
        args.review_dir,
    )

    print()
    print("=" * 72)
    print("DONE")
    print("=" * 72)

    print(
        f"Candidate JSONL: {args.output}"
    )

    print(
        f"Review directory: {args.review_dir}"
    )

    print(
        f"Cases processed: {len(records)}"
    )


if __name__ == "__main__":
    main()