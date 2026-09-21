"""Save the diagnostic figures the model card references: ROC, PR, confusion matrix,
reliability curve and SHAP global importance. Agg backend: safe on a headless CI runner."""

from __future__ import annotations

from pathlib import Path

import matplotlib
import numpy as np
import pandas as pd
from numpy.typing import ArrayLike

matplotlib.use("Agg")
import matplotlib.pyplot as plt
from sklearn.metrics import (
    ConfusionMatrixDisplay,
    PrecisionRecallDisplay,
    RocCurveDisplay,
)

from copilot_ml.evaluation.calibration import ReliabilityCurve


def save_prediction_figures(
    y_true: ArrayLike, y_prob: ArrayLike, threshold: float, out_dir: Path
) -> list[str]:
    out_dir.mkdir(parents=True, exist_ok=True)
    written = []
    y_prob = np.asarray(y_prob, dtype=float)

    fig, ax = plt.subplots(figsize=(5, 4))
    RocCurveDisplay.from_predictions(y_true, y_prob, ax=ax)
    ax.set_title("ROC curve (test)")
    fig.tight_layout()
    fig.savefig(out_dir / "roc_curve.png", dpi=120)
    plt.close(fig)
    written.append("roc_curve.png")

    fig, ax = plt.subplots(figsize=(5, 4))
    PrecisionRecallDisplay.from_predictions(y_true, y_prob, ax=ax)
    ax.set_title("Precision-recall curve (test)")
    fig.tight_layout()
    fig.savefig(out_dir / "pr_curve.png", dpi=120)
    plt.close(fig)
    written.append("pr_curve.png")

    y_pred = [int(p >= threshold) for p in y_prob]
    fig, ax = plt.subplots(figsize=(4, 4))
    ConfusionMatrixDisplay.from_predictions(
        y_true, y_pred, display_labels=["legitimate", "phishing"], ax=ax, colorbar=False
    )
    ax.set_title(f"Confusion matrix (test, threshold={threshold:.3f})")
    fig.tight_layout()
    fig.savefig(out_dir / "confusion_matrix.png", dpi=120)
    plt.close(fig)
    written.append("confusion_matrix.png")

    return written


def save_reliability_figure(curve: ReliabilityCurve, out_dir: Path) -> str:
    out_dir.mkdir(parents=True, exist_ok=True)
    fig, ax = plt.subplots(figsize=(4, 4))
    ax.plot(curve.bin_predicted_mean, curve.bin_true_rate, marker="o", label="model")
    ax.plot([0, 1], [0, 1], linestyle="--", color="gray", label="perfect calibration")
    ax.set_xlabel("Mean predicted probability")
    ax.set_ylabel("Observed phishing rate")
    ax.legend()
    ax.set_title("Reliability curve (validation)")
    fig.tight_layout()
    fig.savefig(out_dir / "calibration_curve.png", dpi=120)
    plt.close(fig)
    return "calibration_curve.png"


def save_shap_figure(global_importance: pd.DataFrame, out_dir: Path, top_n: int = 15) -> str:
    out_dir.mkdir(parents=True, exist_ok=True)
    top = global_importance.head(top_n).iloc[::-1]
    fig, ax = plt.subplots(figsize=(6, 5))
    ax.barh(top["feature"], top["mean_abs_shap"])
    ax.set_xlabel("mean |SHAP value|")
    ax.set_title("Global feature importance (SHAP, champion model)")
    fig.tight_layout()
    fig.savefig(out_dir / "shap_global_importance.png", dpi=120)
    plt.close(fig)
    return "shap_global_importance.png"
