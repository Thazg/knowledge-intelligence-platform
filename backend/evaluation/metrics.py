from __future__ import annotations

from dataclasses import dataclass
from collections import defaultdict

from backend.evaluation.retrieval_evaluator import (
    EvaluationResult,
)


@dataclass(frozen=True)
class RetrievalMetrics:
    cases: int
    hit_at_1: float
    hit_at_3: float
    hit_at_5: float
    hit_at_10: float
    mrr: float


def mean(
    values: list[float],
) -> float:
    if not values:
        return 0.0

    return sum(values) / len(values)


def calculate_metrics(
    results: list[EvaluationResult],
) -> RetrievalMetrics:
    if not results:
        return RetrievalMetrics(
            cases=0,
            hit_at_1=0.0,
            hit_at_3=0.0,
            hit_at_5=0.0,
            hit_at_10=0.0,
            mrr=0.0,
        )

    return RetrievalMetrics(
        cases=len(results),
        hit_at_1=mean([
            float(result.hit_at_k(1))
            for result in results
        ]),
        hit_at_3=mean([
            float(result.hit_at_k(3))
            for result in results
        ]),
        hit_at_5=mean([
            float(result.hit_at_k(5))
            for result in results
        ]),
        hit_at_10=mean([
            float(result.hit_at_k(10))
            for result in results
        ]),
        mrr=mean([
            result.reciprocal_rank
            for result in results
        ]),
    )


def group_results_by_category(
    results: list[EvaluationResult],
) -> dict[str, list[EvaluationResult]]:
    grouped: dict[
        str,
        list[EvaluationResult],
    ] = defaultdict(list)

    for result in results:
        category = (
            result.category
            if result.category
            else "uncategorized"
        )

        grouped[category].append(
            result
        )

    return dict(grouped)


def calculate_metrics_by_category(
    results: list[EvaluationResult],
) -> dict[str, RetrievalMetrics]:
    grouped_results = (
        group_results_by_category(
            results
        )
    )

    return {
        category: calculate_metrics(
            category_results
        )
        for category, category_results
        in grouped_results.items()
    }


def print_metrics(
    title: str,
    metrics: RetrievalMetrics,
) -> None:
    print()
    print("=" * 80)
    print(title)
    print("=" * 80)
    print(
        f"Cases  : {metrics.cases}"
    )
    print(
        f"Hit@1  : {metrics.hit_at_1:.4f}"
    )
    print(
        f"Hit@3  : {metrics.hit_at_3:.4f}"
    )
    print(
        f"Hit@5  : {metrics.hit_at_5:.4f}"
    )
    print(
        f"Hit@10 : {metrics.hit_at_10:.4f}"
    )
    print(
        f"MRR    : {metrics.mrr:.4f}"
    )