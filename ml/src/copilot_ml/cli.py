"""Command-line entry point: `copilot-ml data download | build`."""

from __future__ import annotations

import logging

import typer

from copilot_ml.config import MLSettings
from copilot_ml.data.download import ensure_archive
from copilot_ml.data.pipeline import build_dataset
from copilot_ml.data.sources import PHIUSIIL

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
