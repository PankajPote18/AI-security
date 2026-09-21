"""Render the human-readable model card from an `ExperimentResult` plus SHAP global importance."""

from __future__ import annotations

from datetime import date

import pandas as pd

from copilot_ml.evaluation.comparison import PRODUCTION_VIEW, CandidateResult
from copilot_ml.evaluation.metrics import ClassificationMetrics
from copilot_ml.evaluation.prevalence import PrevalenceAdjustedPrecision
from copilot_ml.reporting import format_percent as pct
from copilot_ml.reporting import render_table as table
from copilot_ml.training.experiment import ExperimentResult


def _rubric_section() -> str:
    return (
        "## 1. Selection rubric (fixed before results were seen)\n\n"
        "Primary metric: **PR-AUC on the validation split**. Tie-breaks, in order: lower Brier "
        "score (calibration), lower prediction latency, smaller artifact, and simplicity "
        "(logistic regression before random forest before XGBoost). The champion is chosen "
        f"**only among `{PRODUCTION_VIEW}`-view candidates** - see §2."
    )


def _shortcut_recap_section() -> str:
    return (
        "## 2. Why the champion is a `host`-view model\n\n"
        "The M1.1 data card's shortcut audit found every legitimate URL in this dataset is a "
        "bare `https://host` homepage, while phishing URLs commonly have paths/queries/plain "
        "http. A model trained on the `full` feature view (path, query, scheme included) can "
        "reach very high accuracy on this data by recognising *how the dataset was sourced* "
        "rather than *what phishing looks like*, which would not generalise to real traffic "
        "(a legitimate URL with a path is common in the real world; here there are none). "
        "The comparison table below reports both views side by side so this gap is visible, "
        "but only a `host`-view candidate can become the champion."
    )


def _comparison_section(candidates: list[CandidateResult]) -> str:
    rows = [
        [
            c.model_name,
            c.view,
            f"{c.metrics.pr_auc:.4f}",
            f"{c.metrics.roc_auc:.4f}",
            f"{c.metrics.f1:.4f}",
            f"{c.metrics.brier:.4f}",
            f"{c.predict_seconds * 1000:.1f} ms",
            f"{c.artifact_size_bytes / 1024:.0f} KB",
        ]
        for c in candidates
    ]
    return (
        "## 3. Candidate comparison (validation split, threshold 0.5, all 6 model x view "
        "combinations, ranked by the rubric)\n\n"
        + table(
            [
                "Model",
                "View",
                "PR-AUC",
                "ROC-AUC",
                "F1",
                "Brier",
                "Predict latency",
                "Artifact size",
            ],
            rows,
        )
    )


def _champion_section(result: ExperimentResult) -> str:
    champion = result.champion
    return (
        "## 4. Champion\n\n"
        f"**`{champion.model_name}` on the `{champion.view}` view.** Validation "
        f"PR-AUC {champion.metrics.pr_auc:.4f}, ROC-AUC {champion.metrics.roc_auc:.4f}.\n\n"
        f"Operating threshold: **{result.threshold:.4f}** (probability of phishing at or above "
        "this is classified phishing), chosen on validation to maximise F1."
    )


def _final_metrics_section(result: ExperimentResult) -> str:
    def metrics_rows(
        m: ClassificationMetrics, prevalence: PrevalenceAdjustedPrecision
    ) -> list[list[str]]:
        return [
            ["Accuracy", f"{m.accuracy:.4f}"],
            ["Precision (this data's ~43% prevalence)", f"{m.precision:.4f}"],
            [
                f"Precision (rebased to {pct(prevalence.assumed_prevalence)} prevalence)",
                f"{prevalence.precision_at_prevalence:.4f}",
            ],
            ["Recall", f"{m.recall:.4f}"],
            ["F1", f"{m.f1:.4f}"],
            ["ROC-AUC", f"{m.roc_auc:.4f}"],
            ["PR-AUC", f"{m.pr_auc:.4f}"],
            ["Brier score", f"{m.brier:.4f}"],
            ["Confusion matrix (tn, fp, fn, tp)", f"{m.tn}, {m.fp}, {m.fn}, {m.tp}"],
        ]

    return (
        "## 5. Final metrics at the chosen threshold\n\n"
        "### Validation (used to pick the champion, threshold and this section's numbers)\n\n"
        + table(
            ["Metric", "Value"], metrics_rows(result.val_metrics, result.val_prevalence_adjusted)
        )
        + "\n\n### Test (touched exactly once, after every other decision was made)\n\n"
        + table(
            ["Metric", "Value"], metrics_rows(result.test_metrics, result.test_prevalence_adjusted)
        )
        + "\n\nRebased precision matters more than the raw figure: at real-world prevalence, most "
        "URLs are legitimate, so even a low false-positive rate produces many false alarms per "
        "true phishing hit. The rebased number is the honest one to quote."
    )


def _calibration_section(result: ExperimentResult) -> str:
    curve = result.val_reliability
    rows = [
        [f"{p:.3f}", f"{t:.3f}"]
        for p, t in zip(curve.bin_predicted_mean, curve.bin_true_rate, strict=True)
    ]
    return (
        "## 6. Calibration\n\n"
        "Reliability curve on validation (predicted-probability bin mean vs. observed phishing "
        f"rate in that bin; perfectly calibrated means the two columns match). Brier score: "
        f"**{result.val_metrics.brier:.4f}**.\n\n"
        + table(["Predicted mean", "Observed rate"], rows)
        + "\n\nNo calibration layer is applied before export. This dataset's ~43% phishing "
        "prevalence is far from real traffic, so a calibrator fit here would calibrate "
        "probabilities *to this dataset*, not to production - it would not close the gap that "
        "matters. The prevalence rebasing in §5 addresses that gap directly instead."
    )


def _shap_section(global_importance: pd.DataFrame, top_n: int = 15) -> str:
    rows = [
        [feature, f"{value:.4f}"]
        for feature, value in global_importance.head(top_n).itertuples(index=False)
    ]
    return (
        "## 7. Explainability (SHAP)\n\n"
        "Mean |SHAP value| over a validation sample, in the model's native output units "
        "(log-odds for logistic regression and XGBoost; probability for random forest - SHAP "
        "explainer defaults differ by model type). Larger = more influence on the prediction, "
        "in either direction.\n\n" + table(["Feature", "Mean |SHAP value|"], rows)
    )


def _limitations_section() -> str:
    return (
        "## 8. Limitations\n\n"
        "- Trained on one dataset (PhiUSIIL, see the data card) collected at one point in time; "
        "phishing URL patterns evolve, and this model will drift.\n"
        "- URL-only: it has no access to page content, redirects, DNS, WHOIS or reputation data "
        "(those arrive in Stage 2+ as separate, non-ML evidence).\n"
        "- The legitimate class here is entirely bare homepages; a legitimate URL with a path "
        "or query is out-of-distribution for this model in a way real traffic will not be. An "
        "external validation set with legitimate URLs that have paths would test this directly "
        "(tracked as follow-up work, not yet available).\n"
        "- Probabilities reflect this dataset's ~43% phishing prevalence; see §5 and §6."
    )


def render_model_card(
    result: ExperimentResult, global_importance: pd.DataFrame, dataset_key: str, built_on: date
) -> str:
    sections = [
        "# Model Card — Phishing URL Classifier",
        f"_Generated by `copilot-ml train` on {built_on.isoformat()}, from the `{dataset_key}` "
        "dataset split (see `data_card.md`). Do not edit by hand; rebuild instead._",
        _rubric_section(),
        _shortcut_recap_section(),
        _comparison_section(result.candidates),
        _champion_section(result),
        _final_metrics_section(result),
        _calibration_section(result),
        _shap_section(global_importance),
        _limitations_section(),
    ]
    return "\n\n".join(sections) + "\n"
