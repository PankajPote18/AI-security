from copilot_ml.evaluation.metrics import compute_metrics
from copilot_ml.evaluation.threshold import select_threshold_at_min_recall, select_threshold_max_f1

_Y_TRUE = [0] * 20 + [1] * 20
_Y_PROB = [i / 20 for i in range(20)] + [0.5 + i / 40 for i in range(20)]  # separable-ish


def test_max_f1_threshold_beats_the_default_0_5_on_this_data() -> None:
    threshold = select_threshold_max_f1(_Y_TRUE, _Y_PROB)
    at_chosen = compute_metrics(_Y_TRUE, _Y_PROB, threshold)
    at_default = compute_metrics(_Y_TRUE, _Y_PROB, 0.5)
    assert at_chosen.f1 >= at_default.f1


def test_min_recall_threshold_meets_the_floor() -> None:
    threshold = select_threshold_at_min_recall(_Y_TRUE, _Y_PROB, min_recall=0.9)
    metrics = compute_metrics(_Y_TRUE, _Y_PROB, threshold)
    assert metrics.recall >= 0.9


def test_min_recall_threshold_prefers_highest_precision_within_the_floor() -> None:
    loose = select_threshold_at_min_recall(_Y_TRUE, _Y_PROB, min_recall=0.5)
    strict = select_threshold_at_min_recall(_Y_TRUE, _Y_PROB, min_recall=0.95)
    assert strict <= loose  # a tighter recall floor cannot raise the threshold


def test_unreachable_recall_floor_returns_zero() -> None:
    # No threshold can reach recall > 1.0; the function must not raise.
    assert select_threshold_at_min_recall(_Y_TRUE, _Y_PROB, min_recall=1.5) == 0.0
