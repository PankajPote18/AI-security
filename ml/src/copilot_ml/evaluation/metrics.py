"""Point-in-time classification metrics at a fixed decision threshold, plus threshold-free
ranking metrics (ROC-AUC, PR-AUC) and calibration error (Brier score)."""

from __future__ import annotations

from dataclasses import asdict, dataclass
from typing import Any

import numpy as np
from numpy.typing import ArrayLike
from sklearn.metrics import (
    accuracy_score,
    average_precision_score,
    brier_score_loss,
    confusion_matrix,
    f1_score,
    precision_score,
    recall_score,
    roc_auc_score,
)


@dataclass(frozen=True)
class ClassificationMetrics:
    threshold: float
    n: int
    accuracy: float
    precision: float
    recall: float
    f1: float
    roc_auc: float
    pr_auc: float
    brier: float
    tn: int
    fp: int
    fn: int
    tp: int

    def as_dict(self) -> dict[str, Any]:
        return asdict(self)


def compute_metrics(
    y_true: ArrayLike, y_prob: ArrayLike, threshold: float
) -> ClassificationMetrics:
    y_true_arr = np.asarray(y_true, dtype=int)
    y_prob_arr = np.asarray(y_prob, dtype=float)
    y_pred = (y_prob_arr >= threshold).astype(int)

    tn, fp, fn, tp = confusion_matrix(y_true_arr, y_pred, labels=[0, 1]).ravel()
    both_classes_present = len(np.unique(y_true_arr)) > 1

    return ClassificationMetrics(
        threshold=threshold,
        n=len(y_true_arr),
        accuracy=float(accuracy_score(y_true_arr, y_pred)),
        precision=float(precision_score(y_true_arr, y_pred, zero_division=0)),
        recall=float(recall_score(y_true_arr, y_pred, zero_division=0)),
        f1=float(f1_score(y_true_arr, y_pred, zero_division=0)),
        roc_auc=float(roc_auc_score(y_true_arr, y_prob_arr))
        if both_classes_present
        else float("nan"),
        pr_auc=float(average_precision_score(y_true_arr, y_prob_arr))
        if both_classes_present
        else float("nan"),
        brier=float(brier_score_loss(y_true_arr, y_prob_arr)),
        tn=int(tn),
        fp=int(fp),
        fn=int(fn),
        tp=int(tp),
    )
