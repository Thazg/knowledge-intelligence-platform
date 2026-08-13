from __future__ import annotations

import json
import re
from dataclasses import asdict, dataclass
from pathlib import Path

from backend.chunking.serializer import (
    ChunkSerializer,
)
from backend.embedding.embedder import (
    LocalEmbedder,
)
from backend.retrieval.bm25_retriever import (
    BM25Retriever,
)
from backend.retrieval.dense_retriever import (
    DenseRetriever,
)
from backend.vector_store.qdrant_store import (
    QdrantVectorStore,
)


PROJECT_ROOT = Path(__file__).resolve().parents[1]

GROUND_TRUTH_PATH = (
    PROJECT_ROOT
    / "benchmarks"
    / "retrieval"
    / "routing"
    / "ground_truth_v1.jsonl"
)

LABELS_PATH = (
    PROJECT_ROOT
    / "benchmarks"
    / "retrieval"
    / "routing"
    / "preferred_strategy_v1.jsonl"
)

CHUNKS_PATH = (
    PROJECT_ROOT
    / "data"
    / "processed"
    / "chunks_fixed.jsonl"
)

OUTPUT_PATH = (
    PROJECT_ROOT
    / "benchmarks"
    / "retrieval"
    / "routing"
    / "combined_signal_audit_v1.json"
)

COLLECTION_NAME = (
    "enterprise_knowledge_fixed_bge_small"
)

EMBEDDING_MODEL = (
    "BAAI/bge-small-en-v1.5"
)

RETRIEVAL_K = 50
DISAGREEMENT_OVERLAP_K = 10
DISAGREEMENT_MAX_OVERLAP = 2


EXPLICIT_CONSTRAINT_PATTERN = re.compile(
    r"\b("
    r"without|while|before|instead of|"
    r"multiple|separate|correct|immediately"
    r")\b",
    re.IGNORECASE,
)


@dataclass(frozen=True)
class RuleMetrics:
    cases: int

    true_positive: int
    false_positive: int
    true_negative: int
    false_negative: int

    precision: float
    recall: float
    false_positive_rate: float
    activation_rate: float


def load_jsonl(
    path: Path,
) -> list[dict]:
    return [
        json.loads(line)
        for line in path.read_text(
            encoding="utf-8"
        ).splitlines()
        if line.strip()
    ]


def document_key(
    result,
) -> tuple[str, str]:
    return (
        result.source.casefold(),
        result.relative_path
        .replace("\\", "/")
        .casefold(),
    )


def unique_documents(
    results,
    limit: int,
) -> list[tuple[str, str]]:
    documents = []
    seen = set()

    for result in results:
        key = document_key(result)

        if key in seen:
            continue

        seen.add(key)
        documents.append(key)

        if len(documents) >= limit:
            break

    return documents


def overlap_at_k(
    dense_documents,
    bm25_documents,
    k: int,
) -> int:
    return len(
        set(dense_documents[:k])
        & set(bm25_documents[:k])
    )


def safe_ratio(
    numerator: int,
    denominator: int,
) -> float:
    if denominator == 0:
        return 0.0

    return numerator / denominator


def calculate_rule_metrics(
    rows: list[dict],
    rule_name: str,
) -> RuleMetrics:
    tp = 0
    fp = 0
    tn = 0
    fn = 0

    for row in rows:
        predicted_high_quality = bool(
            row["rules"][rule_name]
        )

        actual_high_quality = (
            row["preferred_strategy"]
            == "high_quality"
        )

        if (
            predicted_high_quality
            and actual_high_quality
        ):
            tp += 1

        elif (
            predicted_high_quality
            and not actual_high_quality
        ):
            fp += 1

        elif (
            not predicted_high_quality
            and actual_high_quality
        ):
            fn += 1

        else:
            tn += 1

    return RuleMetrics(
        cases=len(rows),
        true_positive=tp,
        false_positive=fp,
        true_negative=tn,
        false_negative=fn,
        precision=safe_ratio(
            tp,
            tp + fp,
        ),
        recall=safe_ratio(
            tp,
            tp + fn,
        ),
        false_positive_rate=safe_ratio(
            fp,
            fp + tn,
        ),
        activation_rate=safe_ratio(
            tp + fp,
            len(rows),
        ),
    )


def main() -> None:
    ground_truth_rows = load_jsonl(
        GROUND_TRUTH_PATH
    )

    label_rows = load_jsonl(
        LABELS_PATH
    )

    ground_truth = {
        row["case_id"]: row
        for row in ground_truth_rows
    }

    assert len(ground_truth) == 45
    assert len(label_rows) == 45

    serializer = ChunkSerializer()

    chunks = serializer.load_jsonl(
        CHUNKS_PATH
    )

    print(
        f"Loaded chunks: {len(chunks):,}"
    )

    embedder = LocalEmbedder(
        model_name=EMBEDDING_MODEL,
    )

    vector_store = QdrantVectorStore(
        collection_name=COLLECTION_NAME,
        vector_size=embedder.dimension,
    )

    dense = DenseRetriever(
        embedder=embedder,
        vector_store=vector_store,
    )

    bm25 = BM25Retriever(
        chunks=chunks,
    )

    rows = []

    eligible_labels = [
        row
        for row in label_rows
        if row["preferred_strategy"]
        in {
            "standard",
            "high_quality",
        }
    ]

    assert len(eligible_labels) == 43

    for index, label in enumerate(
        eligible_labels,
        start=1,
    ):
        case_id = label["case_id"]
        query = label["query"]

        gt = ground_truth[case_id]

        technologies = gt.get(
            "technologies",
            [],
        )

        multi_technology = (
            len(technologies) >= 2
        )

        explicit_constraint = bool(
            EXPLICIT_CONSTRAINT_PATTERN.search(
                query
            )
        )

        dense_results = dense.retrieve(
            query=query,
            top_k=RETRIEVAL_K,
            max_chunks_per_document=None,
        )

        bm25_results = bm25.retrieve(
            query=query,
            top_k=RETRIEVAL_K,
            max_chunks_per_document=None,
        )

        dense_documents = (
            unique_documents(
                dense_results,
                RETRIEVAL_K,
            )
        )

        bm25_documents = (
            unique_documents(
                bm25_results,
                RETRIEVAL_K,
            )
        )

        overlap_10 = overlap_at_k(
            dense_documents,
            bm25_documents,
            DISAGREEMENT_OVERLAP_K,
        )

        disagreement = (
            overlap_10
            <= DISAGREEMENT_MAX_OVERLAP
        )

        rules = {
            "rule_a": (
                multi_technology
                and explicit_constraint
            ),
            "rule_b": (
                multi_technology
                and disagreement
            ),
            "rule_c": (
                explicit_constraint
                and disagreement
            ),
            "rule_d": (
                (
                    multi_technology
                    or explicit_constraint
                )
                and disagreement
            ),
        }

        rows.append({
            "case_id": case_id,
            "preferred_strategy": (
                label["preferred_strategy"]
            ),
            "features": {
                "multi_technology": (
                    multi_technology
                ),
                "explicit_constraint": (
                    explicit_constraint
                ),
                "overlap_at_10": (
                    overlap_10
                ),
                "retrieval_disagreement": (
                    disagreement
                ),
            },
            "rules": rules,
        })

        print(
            f"[{index:>2}/43] "
            f"{case_id} | "
            f"{label['preferred_strategy']:<12} | "
            f"multi={multi_technology} | "
            f"constraint={explicit_constraint} | "
            f"O10={overlap_10}"
        )

    rule_descriptions = {
        "rule_a": (
            "multi_technology AND "
            "explicit_constraint"
        ),
        "rule_b": (
            "multi_technology AND "
            "retrieval_disagreement"
        ),
        "rule_c": (
            "explicit_constraint AND "
            "retrieval_disagreement"
        ),
        "rule_d": (
            "(multi_technology OR "
            "explicit_constraint) AND "
            "retrieval_disagreement"
        ),
    }

    metrics = {
        rule_name: calculate_rule_metrics(
            rows,
            rule_name,
        )
        for rule_name in rule_descriptions
    }

    print()
    print("=" * 96)
    print(
        "COMBINED ROUTING SIGNAL AUDIT"
    )
    print("=" * 96)

    for rule_name in (
        "rule_a",
        "rule_b",
        "rule_c",
        "rule_d",
    ):
        result = metrics[rule_name]

        print()
        print(
            f"{rule_name.upper()}: "
            f"{rule_descriptions[rule_name]}"
        )
        print("-" * 96)

        print(
            f"TP / FP          : "
            f"{result.true_positive} / "
            f"{result.false_positive}"
        )
        print(
            f"TN / FN          : "
            f"{result.true_negative} / "
            f"{result.false_negative}"
        )
        print(
            f"Precision        : "
            f"{result.precision:.3f}"
        )
        print(
            f"Recall           : "
            f"{result.recall:.3f}"
        )
        print(
            f"False-positive   : "
            f"{result.false_positive_rate:.3f}"
        )
        print(
            f"Activation rate  : "
            f"{result.activation_rate:.3f}"
        )

    report = {
        "experiment": {
            "name": (
                "combined_signal_audit_v1"
            ),
            "cases": len(rows),
            "positive_class": (
                "high_quality"
            ),
            "negative_class": (
                "standard"
            ),
            "coverage_cases_excluded": 2,
        },
        "configuration": {
            "retrieval_k": (
                RETRIEVAL_K
            ),
            "disagreement": {
                "metric": (
                    "document_overlap_at_10"
                ),
                "maximum_overlap": (
                    DISAGREEMENT_MAX_OVERLAP
                ),
            },
            "rules": (
                rule_descriptions
            ),
        },
        "metrics": {
            rule_name: asdict(
                rule_metrics
            )
            for rule_name, rule_metrics
            in metrics.items()
        },
        "cases": rows,
    }

    OUTPUT_PATH.write_text(
        json.dumps(
            report,
            indent=2,
            ensure_ascii=False,
        )
        + "\n",
        encoding="utf-8",
    )

    print()
    print(
        f"Report: {OUTPUT_PATH}"
    )


if __name__ == "__main__":
    main()