"""Calibrate an already-fitted pipeline's probabilities on a disjoint split, and describe how
well-calibrated a set of predictions is (reliability curve + Brier score, already in `metrics`).

Calibration is fit on the *validation* split (the model itself never saw it) and its quality is
then judged on the untouched *test* split, so the reported Brier score is honest.
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Literal

from numpy.typing import ArrayLike
from sklearn.base import BaseEstimator
from sklearn.calibration import CalibratedClassifierCV, calibration_curve
from sklearn.frozen import FrozenEstimator

CalibrationMethod = Literal["sigmoid", "isotonic"]


def calibrate(
    fitted_pipeline: BaseEstimator,
    x_val: ArrayLike,
    y_val: ArrayLike,
    method: CalibrationMethod = "sigmoid",
) -> CalibratedClassifierCV:
    """Wrap an already-fitted pipeline so its `predict_proba` is calibrated on `(x_val, y_val)`.

    Uses only that data for calibration (no internal re-splitting), matching the historical
    `cv="prefit"` behaviour via the current `FrozenEstimator` API.
    """
    calibrated = CalibratedClassifierCV(FrozenEstimator(fitted_pipeline), method=method)
    calibrated.fit(x_val, y_val)
    return calibrated


@dataclass(frozen=True)
class ReliabilityCurve:
    bin_true_rate: list[float]
    bin_predicted_mean: list[float]


def reliability_curve(y_true: ArrayLike, y_prob: ArrayLike, n_bins: int = 10) -> ReliabilityCurve:
    true_rate, predicted_mean = calibration_curve(
        y_true, y_prob, n_bins=n_bins, strategy="quantile"
    )
    return ReliabilityCurve(true_rate.tolist(), predicted_mean.tolist())
