"""Orchestrates dataset build: download -> load -> clean -> verify labels -> split -> write.

I/O happens only here; every step it calls is a pure function that is unit-tested on its own.
"""

from __future__ import annotations

import json
import logging
from collections.abc import Sequence
from datetime import date

import pandas as pd

from copilot_ml.config import SPLIT_NAMES, MLSettings
from copilot_ml.data.audit import shortcut_audit
from copilot_ml.data.card import render_data_card
from copilot_ml.data.cleaning import clean_urls
from copilot_ml.data.download import ensure_archive
from copilot_ml.data.grouping import add_site_column
from copilot_ml.data.labels import verify_label_polarity
from copilot_ml.data.loading import load_labeled_urls
from copilot_ml.data.sources import PHIUSIIL, DatasetSource
from copilot_ml.data.splitting import (
    assert_balanced_splits,
    assert_no_site_leakage,
    assign_splits,
    site_overlap,
    summarize_splits,
)
from copilot_ml.data.summary import DatasetSummary

logger = logging.getLogger(__name__)

MANIFEST_NAME = "split_manifest.json"
CARD_NAME = "data_card.md"
_OUTPUT_COLUMNS = ["source_row", "url", "label", "site"]
_TOP_SITES = 8


def build_dataset(
    settings: MLSettings | None = None,
    source: DatasetSource = PHIUSIIL,
    *,
    allowed_schemes: Sequence[str] = ("https",),
    built_on: date | None = None,
) -> DatasetSummary:
    settings = settings or MLSettings.from_env()
    archive, checksum = ensure_archive(source, settings, allowed_schemes)

    logger.info("Loading %s", archive.name)
    raw = load_labeled_urls(archive, source)

    logger.info("Cleaning %d rows", len(raw))
    cleaned, cleaning = clean_urls(raw)
    polarity = verify_label_polarity(cleaned)

    logger.info("Splitting %d rows by site", len(cleaned))
    grouped = add_site_column(cleaned)
    split = assign_splits(grouped, settings)
    assert_no_site_leakage(split)
    assert_balanced_splits(split, settings)

    summary = DatasetSummary(
        source=source,
        archive_sha256=checksum,
        archive_bytes=archive.stat().st_size,
        cleaning=cleaning,
        polarity=polarity,
        seed=settings.seed,
        n_folds=settings.n_folds,
        split_folds=dict(settings.split_folds),
        splits=summarize_splits(split),
        site_overlap=site_overlap(split),
        largest_sites=[
            (str(site), int(count))
            for site, count in split["site"].value_counts().head(_TOP_SITES).items()
        ],
        indicators=shortcut_audit(split),
    )
    _write_outputs(split, summary, settings, built_on or date.today())
    return summary


def _write_outputs(
    split: pd.DataFrame, summary: DatasetSummary, settings: MLSettings, built_on: date
) -> None:
    settings.processed_dir.mkdir(parents=True, exist_ok=True)
    settings.reports_dir.mkdir(parents=True, exist_ok=True)

    for name in SPLIT_NAMES:
        part = split.loc[split["split"] == name, _OUTPUT_COLUMNS].reset_index(drop=True)
        part.to_parquet(settings.processed_dir / f"{name}.parquet", index=False)

    manifest = json.dumps(summary.manifest(), indent=2, sort_keys=True) + "\n"
    (settings.processed_dir / MANIFEST_NAME).write_text(manifest, encoding="utf-8")
    (settings.reports_dir / CARD_NAME).write_text(
        render_data_card(summary, built_on), encoding="utf-8"
    )
    logger.info("Wrote splits, manifest and data card")
