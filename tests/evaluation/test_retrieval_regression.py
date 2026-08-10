import json
from pathlib import Path

from backend.evaluation.metrics import RetrievalMetrics
from scripts.check_retrieval_regression import (
    check_regression,
    load_baseline,
)


def make_metrics(
    *,
    hit_at_1: float,
    hit_at_10: float,
    recall_at_10: float,
    ndcg_at_10: float,
    mrr: float,
) -> RetrievalMetrics:
    return RetrievalMetrics(
        cases=100,
        hit_at_1=hit_at_1,
        hit_at_3=0.0,
        hit_at_5=0.0,
        hit_at_10=hit_at_10,
        recall_at_3=0.0,
        recall_at_5=0.0,
        recall_at_10=recall_at_10,
        ndcg_at_3=0.0,
        ndcg_at_5=0.0,
        ndcg_at_10=ndcg_at_10,
        mrr=mrr,
    )


BASELINE = {
    "hit_at_1": 0.62,
    "hit_at_10": 0.93,
    "recall_at_10": 0.8392,
    "ndcg_at_10": 0.6788,
    "mrr": 0.7247,
}


def test_check_regression_passes_with_baseline_metrics() -> None:
    current = make_metrics(
        hit_at_1=0.62,
        hit_at_10=0.93,
        recall_at_10=0.8392,
        ndcg_at_10=0.6788,
        mrr=0.7247,
    )

    assert check_regression(
        current=current,
        baseline=BASELINE,
        tolerance=0.02,
    )


def test_check_regression_allows_small_drop() -> None:
    current = make_metrics(
        hit_at_1=0.61,
        hit_at_10=0.92,
        recall_at_10=0.8292,
        ndcg_at_10=0.6688,
        mrr=0.7147,
    )

    assert check_regression(
        current=current,
        baseline=BASELINE,
        tolerance=0.02,
    )


def test_check_regression_fails_when_metric_drops_too_far() -> None:
    current = make_metrics(
        hit_at_1=0.59,
        hit_at_10=0.93,
        recall_at_10=0.8392,
        ndcg_at_10=0.6788,
        mrr=0.7247,
    )

    assert not check_regression(
        current=current,
        baseline=BASELINE,
        tolerance=0.02,
    )

def test_load_baseline_reads_ci_format(
    tmp_path: Path,
) -> None:
    baseline_path = tmp_path / "baseline.json"

    payload = {
        "metrics": BASELINE,
        "regression_tolerance": 0.02,
    }

    baseline_path.write_text(
        json.dumps(payload),
        encoding="utf-8",
    )

    baseline, tolerance = load_baseline(
        baseline_path,
    )

    assert baseline == BASELINE
    assert tolerance == 0.02


def test_load_baseline_reads_full_manifest_format(
    tmp_path: Path,
) -> None:
    manifest_path = tmp_path / "manifest.json"

    payload = {
        "baseline": BASELINE,
        "regression": {
            "tolerance": 0.02,
        },
    }

    manifest_path.write_text(
        json.dumps(payload),
        encoding="utf-8",
    )

    baseline, tolerance = load_baseline(
        manifest_path,
    )

    assert baseline == BASELINE
    assert tolerance == 0.02