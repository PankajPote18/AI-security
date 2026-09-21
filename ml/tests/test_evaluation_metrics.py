import math

from copilot_ml.evaluation.metrics import compute_metrics

_Y_TRUE = [0, 0, 0, 0, 1, 1, 1, 1]
_Y_PROB = [0.1, 0.2, 0.4, 0.6, 0.3, 0.7, 0.8, 0.9]  # one false positive, one false negative @0.5


def test_confusion_matrix_and_derived_metrics_at_a_threshold() -> None:
    m = compute_metrics(_Y_TRUE, _Y_PROB, threshold=0.5)
    assert (m.tn, m.fp, m.fn, m.tp) == (3, 1, 1, 3)
    assert m.accuracy == 6 / 8
    assert m.precision == 3 / 4
    assert m.recall == 3 / 4
    assert m.f1 == 3 / 4
    assert m.n == 8


def test_higher_threshold_reduces_or_keeps_recall_and_increases_or_keeps_precision() -> None:
    low = compute_metrics(_Y_TRUE, _Y_PROB, threshold=0.1)
    high = compute_metrics(_Y_TRUE, _Y_PROB, threshold=0.9)
    assert high.recall <= low.recall
    assert high.tp <= low.tp


def test_threshold_free_metrics_are_unaffected_by_threshold() -> None:
    a = compute_metrics(_Y_TRUE, _Y_PROB, threshold=0.1)
    b = compute_metrics(_Y_TRUE, _Y_PROB, threshold=0.9)
    assert a.roc_auc == b.roc_auc
    assert a.pr_auc == b.pr_auc
    assert a.brier == b.brier


def test_single_class_labels_do_not_raise_and_mark_auc_as_nan() -> None:
    m = compute_metrics([0, 0, 0], [0.1, 0.2, 0.3], threshold=0.5)
    assert math.isnan(m.roc_auc)
    assert math.isnan(m.pr_auc)
    assert m.accuracy == 1.0


def test_perfect_predictions_give_brier_zero() -> None:
    m = compute_metrics([0, 1], [0.0, 1.0], threshold=0.5)
    assert m.brier == 0.0
