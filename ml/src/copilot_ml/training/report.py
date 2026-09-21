"""Orchestrates a full training run: fit + compare every candidate, pick and evaluate the
champion, render `model_card.md` + `metrics.json` + figures, and export the artifact.

This is what `copilot-ml train` calls. Kept separate from the CLI so it is testable directly.
"""

from __future__ import annotations

import json
from dataclasses import dataclass
from datetime import date
from pathlib import Path

import pandas as pd

from copilot_ml.config import MLSettings
from copilot_ml.data.pipeline import MANIFEST_NAME
from copilot_ml.data.sources import PHIUSIIL
from copilot_ml.evaluation.model_card import render_model_card
from copilot_ml.evaluation.plots import (
    save_prediction_figures,
    save_reliability_figure,
    save_shap_figure,
)
from copilot_ml.explain.shap_explainer import global_importance
from copilot_ml.training.experiment import ExperimentResult, run_experiment
from copilot_ml.training.export import export_model, sample_background

MODEL_CARD_NAME = "model_card.md"
METRICS_NAME = "metrics.json"


def _dataset_archive_sha256(settings: MLSettings) -> str:
    manifest = json.loads((settings.processed_dir / MANIFEST_NAME).read_text("utf-8"))
    return str(manifest["source"]["archive_sha256"])


def _write_metrics_json(result: ExperimentResult, out_path: Path) -> None:
    payload = {
        "champion": {
            "model_name": result.champion.model_name,
            "view": result.champion.view,
            "threshold": result.threshold,
        },
        "candidates": [
            {
                "model_name": c.model_name,
                "view": c.view,
                "fit_seconds": c.fit_seconds,
                "predict_seconds": c.predict_seconds,
                "artifact_size_bytes": c.artifact_size_bytes,
                **c.metrics.as_dict(),
            }
            for c in result.candidates
        ],
        "val_metrics": result.val_metrics.as_dict(),
        "test_metrics": result.test_metrics.as_dict(),
        "val_prevalence_adjusted_precision": vars(result.val_prevalence_adjusted),
        "test_prevalence_adjusted_precision": vars(result.test_prevalence_adjusted),
    }
    out_path.write_text(json.dumps(payload, indent=2, sort_keys=True) + "\n", encoding="utf-8")


@dataclass(frozen=True)
class TrainingRunOutcome:
    result: ExperimentResult
    model_dir: Path


def run_and_export(
    settings: MLSettings | None = None, seed: int | None = None
) -> TrainingRunOutcome:
    settings = settings or MLSettings.from_env()
    seed = seed if seed is not None else settings.seed

    train_df = pd.read_parquet(settings.processed_dir / "train.parquet")
    val_df = pd.read_parquet(settings.processed_dir / "val.parquet")
    test_df = pd.read_parquet(settings.processed_dir / "test.parquet")

    result = run_experiment(train_df, val_df, test_df, seed)
    importance = global_importance(result.champion_pipeline, result.val_features)

    settings.reports_dir.mkdir(parents=True, exist_ok=True)
    figures_dir = settings.reports_dir / "figures"
    save_prediction_figures(test_df["label"], result.test_proba, result.threshold, figures_dir)
    save_reliability_figure(result.val_reliability, figures_dir)
    save_shap_figure(importance, figures_dir)

    (settings.reports_dir / MODEL_CARD_NAME).write_text(
        render_model_card(result, importance, dataset_key=PHIUSIIL.key, built_on=date.today()),
        encoding="utf-8",
    )
    _write_metrics_json(result, settings.reports_dir / METRICS_NAME)

    background = sample_background(result.train_features, train_df["label"].astype(int))
    model_dir = settings.home / "models"
    export_model(
        result.champion_pipeline,
        model_dir,
        model_name=result.champion.model_name,
        view=result.champion.view,
        threshold=result.threshold,
        dataset_archive_sha256=_dataset_archive_sha256(settings),
        val_metrics=result.val_metrics.as_dict(),
        test_metrics=result.test_metrics.as_dict(),
        background=background,
    )
    return TrainingRunOutcome(result=result, model_dir=model_dir)
