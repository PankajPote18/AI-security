"""Command-line entry point: `copilot-ml data download|build`, `train`, `predict`."""

from __future__ import annotations

import logging

import typer

from copilot_ml.artifact import ARTIFACT_FILENAME
from copilot_ml.config import MLSettings
from copilot_ml.data.download import ensure_archive
from copilot_ml.data.pipeline import build_dataset
from copilot_ml.data.sources import PHIUSIIL
from copilot_ml.inference.predictor import ArtifactIntegrityError, Predictor
from copilot_ml.training.report import run_and_export

app = typer.Typer(no_args_is_help=True, help="Phishing URL ML pipeline.")
data_app = typer.Typer(no_args_is_help=True, help="Dataset acquisition and preparation.")
app.add_typer(data_app, name="data")


@app.callback()
def _configure_logging() -> None:
    logging.basicConfig(level=logging.INFO, format="%(levelname)s %(name)s: %(message)s")


@data_app.command("download")
def download() -> None:
    """Download the dataset archive and verify (or pin) its checksum."""
    archive, checksum = ensure_archive(PHIUSIIL, MLSettings.from_env())
    typer.echo(f"{archive}  sha256={checksum}")


@data_app.command("build")
def build() -> None:
    """Download if needed, clean, split by site, and write splits + manifest + data card."""
    settings = MLSettings.from_env()
    summary = build_dataset(settings)
    for name, part in summary.splits.items():
        typer.echo(
            f"{name:<5} rows={part.rows:>7,}  phishing={part.phishing_rate:6.2%}  "
            f"sites={part.sites:>7,}"
        )
    typer.echo(f"Wrote {settings.processed_dir} and {settings.reports_dir / 'data_card.md'}")


@app.command("train")
def train() -> None:
    """Train and compare every model x feature-view candidate, pick the champion, evaluate it
    on validation then test (once), and export it plus model_card.md/metrics.json/figures."""
    settings = MLSettings.from_env()
    outcome = run_and_export(settings)
    champion, result = outcome.result.champion, outcome.result
    typer.echo(
        f"Champion: {champion.model_name} ({champion.view} view), threshold={result.threshold:.4f}"
    )
    typer.echo(
        f"Validation: PR-AUC={result.val_metrics.pr_auc:.4f} F1={result.val_metrics.f1:.4f}  |  "
        f"Test: PR-AUC={result.test_metrics.pr_auc:.4f} F1={result.test_metrics.f1:.4f}"
    )
    typer.echo(f"Exported to {outcome.model_dir}")
    typer.echo(f"Reports written to {settings.reports_dir}")


@app.command("predict")
def predict(url: str) -> None:
    """Score a single URL with the exported model."""
    settings = MLSettings.from_env()
    model_dir = settings.home / "models"
    try:
        predictor = Predictor.load(model_dir)
    except FileNotFoundError as error:
        raise typer.BadParameter(
            f"No exported model at {model_dir / ARTIFACT_FILENAME}. Run `copilot-ml train` first."
        ) from error
    except ArtifactIntegrityError as error:
        raise typer.BadParameter(str(error)) from error

    prediction = predictor.predict(url)
    typer.echo(f"URL: {prediction.url}")
    typer.echo(
        f"Phishing probability: {prediction.probability:.4f}"
        f"  (threshold {prediction.threshold:.4f})"
    )
    typer.echo(f"Label: {'PHISHING' if prediction.label else 'legitimate'}")
    typer.echo("Top contributions (feature, transformed value, SHAP value):")
    for c in prediction.top_contributions:
        typer.echo(f"  {c.feature:<28} value={c.transformed_value:8.3f}  shap={c.shap_value:+.4f}")
