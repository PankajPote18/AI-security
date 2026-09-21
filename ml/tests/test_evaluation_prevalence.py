import pytest

from copilot_ml.evaluation.metrics import compute_metrics
from copilot_ml.evaluation.prevalence import (
    false_positive_rate,
    precision_at_prevalence,
    rebase_precision,
)


def test_false_positive_rate_basic() -> None:
    assert false_positive_rate(fp=10, tn=90) == 0.1
    assert false_positive_rate(fp=0, tn=0) == 0.0  # no negatives seen: defined as 0, not NaN


def test_precision_at_matching_prevalence_equals_recall_over_recall_plus_fpr() -> None:
    # At prevalence == recall's own class balance, the formula should reduce sensibly.
    precision = precision_at_prevalence(recall=0.8, fpr=0.1, prevalence=0.5)
    assert precision == pytest.approx(0.8 / (0.8 + 0.1))


def test_lower_prevalence_gives_lower_precision_for_the_same_detector() -> None:
    high_prevalence = precision_at_prevalence(recall=0.9, fpr=0.05, prevalence=0.5)
    low_prevalence = precision_at_prevalence(recall=0.9, fpr=0.05, prevalence=0.01)
    assert low_prevalence < high_prevalence


def test_perfect_detector_has_precision_one_regardless_of_prevalence() -> None:
    assert precision_at_prevalence(recall=1.0, fpr=0.0, prevalence=0.001) == 1.0


def test_rebase_precision_uses_the_metrics_confusion_matrix() -> None:
    y_true = [0] * 95 + [1] * 5  # 5% prevalence in this evaluation sample
    y_prob = [0.1] * 90 + [0.9] * 5 + [0.9] * 5  # 5 false positives, perfect recall
    metrics = compute_metrics(y_true, y_prob, threshold=0.5)
    adjusted = rebase_precision(metrics, prevalence=0.01)

    assert adjusted.recall == metrics.recall
    assert adjusted.false_positive_rate == pytest.approx(metrics.fp / (metrics.fp + metrics.tn))
    assert 0.0 <= adjusted.precision_at_prevalence <= 1.0
    # at 1% real-world prevalence, precision is far below this sample's own ~5%-prevalence value
    assert adjusted.precision_at_prevalence < metrics.precision
