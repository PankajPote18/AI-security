import json
from datetime import date

import pandas as pd
import pytest

from copilot_ml.config import SPLIT_NAMES, MLSettings
from copilot_ml.data.download import ChecksumMismatchError
from copilot_ml.data.pipeline import CARD_NAME, MANIFEST_NAME, build_dataset
from copilot_ml.data.sources import PHIUSIIL
from fixture_data import EXPECTED_ROWS_OUT

BUILT_ON = date(2026, 1, 1)


def _read_splits(settings: MLSettings) -> dict[str, pd.DataFrame]:
    return {n: pd.read_parquet(settings.processed_dir / f"{n}.parquet") for n in SPLIT_NAMES}


def test_build_writes_splits_manifest_and_card(settings_with_archive: MLSettings) -> None:
    summary = build_dataset(settings_with_archive, built_on=BUILT_ON)
    settings = settings_with_archive

    splits = _read_splits(settings)
    assert (
        sum(len(part) for part in splits.values()) == EXPECTED_ROWS_OUT == summary.cleaning.rows_out
    )
    assert list(splits["train"].columns) == ["source_row", "url", "label", "site"]

    manifest = json.loads((settings.processed_dir / MANIFEST_NAME).read_text())
    assert manifest["source"]["key"] == PHIUSIIL.key
    assert set(manifest["site_overlap"].values()) == {0}
    assert (settings.reports_dir / CARD_NAME).read_text().startswith("# Data Card")


def test_no_site_is_shared_between_written_splits(settings_with_archive: MLSettings) -> None:
    build_dataset(settings_with_archive, built_on=BUILT_ON)
    splits = _read_splits(settings_with_archive)
    seen: set[str] = set()
    for part in splits.values():
        sites = set(part["site"])
        assert seen.isdisjoint(sites)
        seen |= sites


def test_labels_are_normalised_to_one_means_phishing(settings_with_archive: MLSettings) -> None:
    build_dataset(settings_with_archive, built_on=BUILT_ON)
    everything = pd.concat(_read_splits(settings_with_archive).values())
    phishing_urls = everything.loc[everything["label"] == 1, "url"]
    legit_urls = everything.loc[everything["label"] == 0, "url"]
    assert phishing_urls.str.contains("paypa1|185.220.1|acct-verify").all()
    assert legit_urls.str.contains("legit-site").all()


def test_build_is_reproducible(settings_with_archive: MLSettings) -> None:
    build_dataset(settings_with_archive, built_on=BUILT_ON)
    first = {n: p.copy() for n, p in _read_splits(settings_with_archive).items()}
    first_manifest = (settings_with_archive.processed_dir / MANIFEST_NAME).read_text()

    build_dataset(settings_with_archive, built_on=BUILT_ON)
    for name, part in _read_splits(settings_with_archive).items():
        pd.testing.assert_frame_equal(part, first[name])
    assert (settings_with_archive.processed_dir / MANIFEST_NAME).read_text() == first_manifest


def test_source_content_columns_do_not_leak_into_outputs(
    settings_with_archive: MLSettings,
) -> None:
    build_dataset(settings_with_archive, built_on=BUILT_ON)
    for part in _read_splits(settings_with_archive).values():
        assert "HasFavicon" not in part.columns


def test_changed_archive_fails_the_build(settings_with_archive: MLSettings) -> None:
    build_dataset(settings_with_archive, built_on=BUILT_ON)  # pins the checksum
    archive = settings_with_archive.raw_dir / f"{PHIUSIIL.key}.zip"
    archive.write_bytes(archive.read_bytes() + b"corruption")
    with pytest.raises(ChecksumMismatchError):
        build_dataset(settings_with_archive, built_on=BUILT_ON)


def test_data_card_reports_the_facts_and_the_shortcut_warning(
    settings_with_archive: MLSettings,
) -> None:
    build_dataset(settings_with_archive, built_on=BUILT_ON)
    card = (settings_with_archive.reports_dir / CARD_NAME).read_text(encoding="utf-8")

    assert "2026-01-01" in card
    assert "CC BY 4.0" in card
    assert "polarity check **passed**" in card
    assert "Sites shared between splits (must all be 0)" in card
    assert "WARNING — shortcut learning risk" in card
    assert "not_bare_https_homepage" in card
    assert "external validation set" in card
