"""Pick an operating threshold on the validation split. Never call these on test."""

from __future__ import annotations

import numpy as np
from numpy.typing import ArrayLike
from sklearn.metrics import precision_recall_curve

DEFAULT_THRESHOLD = 0.5


def select_threshold_max_f1(y_true: ArrayLike, y_prob: ArrayLike) -> float:
    precision, recall, thresholds = precision_recall_curve(y_true, y_prob)
    if len(thresholds) == 0:
        return DEFAULT_THRESHOLD
    precision, recall = (
        precision[:-1],
        recall[:-1],
    )  # drop the sentinel point precision_recall_curve adds
    denom = precision + recall
    f1 = np.divide(2 * precision * recall, denom, out=np.zeros_like(denom), where=denom > 0)
    return float(thresholds[int(np.argmax(f1))])


def select_threshold_at_min_recall(
    y_true: ArrayLike, y_prob: ArrayLike, min_recall: float
) -> float:
    """The highest threshold (best precision) whose recall is still >= `min_recall`."""
    _precision, recall, thresholds = precision_recall_curve(y_true, y_prob)
    if len(thresholds) == 0:
        return DEFAULT_THRESHOLD
    eligible = recall[:-1] >= min_recall
    if not eligible.any():
        return 0.0  # even the lowest threshold cannot hit the recall floor
    return float(thresholds[eligible].max())
