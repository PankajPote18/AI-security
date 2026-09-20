import numpy as np
import pandas as pd
import pytest

from copilot_ml.config import SPLIT_NAMES, MLSettings
from copilot_ml.data.grouping import add_site_column
from copilot_ml.data.splitting import (
    SiteLeakageError,
    SplitImbalanceError,
    assert_balanced_splits,
    assert_no_site_leakage,
    assign_splits,
    site_overlap,
    summarize_splits,
)


@pytest.fixture
def split_frame(clean_frame: pd.DataFrame, settings: MLSettings) -> pd.DataFrame:
    return assign_splits(add_site_column(clean_frame), settings)


def test_no_site_appears_in_two_splits(split_frame: pd.DataFrame) -> None:
    assert set(site_overlap(split_frame).values()) == {0}
    assert_no_site_leakage(split_frame)


def test_multi_url_sites_stay_together(split_frame: pd.DataFrame) -> None:
    per_site_splits = split_frame.groupby("site")["split"].nunique()
    assert per_site_splits.max() == 1


def test_every_row_gets_exactly_one_known_split(split_frame: pd.DataFrame) -> None:
    assert set(split_frame["split"]) == set(SPLIT_NAMES)
    assert split_frame["split"].notna().all()


def test_proportions_are_close_to_70_15_15(split_frame: pd.DataFrame) -> None:
    shares = split_frame["split"].value_counts(normalize=True)
    assert 0.60 <= shares["train"] <= 0.80
    assert 0.07 <= shares["val"] <= 0.23
    assert 0.07 <= shares["test"] <= 0.23


def test_every_split_contains_both_classes(split_frame: pd.DataFrame) -> None:
    for summary in summarize_splits(split_frame).values():
        assert summary.phishing > 0
        assert summary.legitimate > 0


def test_split_is_deterministic_for_a_seed_and_changes_with_it(
    clean_frame: pd.DataFrame, settings: MLSettings
) -> None:
    grouped = add_site_column(clean_frame)
    first = assign_splits(grouped, settings)["split"]
    again = assign_splits(grouped, settings)["split"]
    other = assign_splits(grouped, MLSettings(home=settings.home, seed=settings.seed + 1))["split"]
    assert first.equals(again)
    assert not first.equals(other)


def test_leakage_check_detects_a_site_in_two_splits(split_frame: pd.DataFrame) -> None:
    leaked = split_frame.copy()
    donor_site = leaked.loc[leaked["split"] == "train", "site"].iloc[0]
    leaked.loc[leaked["split"] == "test", "site"] = donor_site
    with pytest.raises(SiteLeakageError):
        assert_no_site_leakage(leaked)


def _uneven_frame() -> pd.DataFrame:
    """300 sites of very different sizes (1..60 URLs) plus one giant site, mixed classes."""
    rng = np.random.default_rng(0)
    rows = []
    for site in range(300):
        size = int(rng.integers(1, 61))
        phishing_share = 0.2 if site % 3 else 0.8
        labels = (rng.random(size) < phishing_share).astype(int)
        rows += [
            {"url": f"http://s{site}.com/{i}", "label": lab, "site": f"s{site}.com"}
            for i, lab in enumerate(labels)
        ]
    rows += [
        {"url": f"http://giant.com/{i}", "label": i % 2, "site": "giant.com"} for i in range(400)
    ]
    return pd.DataFrame(rows)


def test_class_ratio_is_preserved_with_uneven_site_sizes(settings: MLSettings) -> None:
    frame = assign_splits(_uneven_frame(), settings)
    overall = frame["label"].mean()
    for summary in summarize_splits(frame).values():
        assert abs(summary.phishing_rate - overall) < 0.06
    assert_no_site_leakage(frame)


def test_a_giant_site_is_never_split(settings: MLSettings) -> None:
    frame = assign_splits(_uneven_frame(), settings)
    assert frame.loc[frame["site"] == "giant.com", "split"].nunique() == 1


def test_largest_sites_are_not_systematically_placed_in_train() -> None:
    # Greedy ties favour low fold ids; the fold->split shuffle must remove that bias.
    frame = _uneven_frame()
    homes = set()
    for seed in range(20):
        assigned = assign_splits(frame, MLSettings(seed=seed))
        homes.add(assigned.loc[assigned["site"] == "giant.com", "split"].iloc[0])
    assert len(homes) > 1


def _singleton_heavy_frame() -> pd.DataFrame:
    """Shaped like the real data: thousands of one-URL sites plus a few large ones."""
    rng = np.random.default_rng(1)
    labels = (rng.random(6000) < 0.4).astype(int)
    rows = [
        {"url": f"http://x{i}.com", "label": lab, "site": f"x{i}.com"}
        for i, lab in enumerate(labels)
    ]
    for big in range(5):
        rows += [
            {"url": f"http://big{big}.com/{i}", "label": int(i % 3 == 0), "site": f"big{big}.com"}
            for i in range(300)
        ]
    return pd.DataFrame(rows)


def test_singleton_heavy_data_fills_every_fold_evenly() -> None:
    # Regression: an objective based on absolute (not incremental) deviation left folds empty and
    # produced 35% / 69% / 31% phishing rates across splits on the real dataset.
    settings = MLSettings(seed=3)
    frame = assign_splits(_singleton_heavy_frame(), settings)

    assert_balanced_splits(frame, settings)  # default (tight) tolerances
    shares = frame["split"].value_counts(normalize=True)
    assert shares["train"] == pytest.approx(0.70, abs=0.01)
    assert shares["val"] == pytest.approx(0.15, abs=0.01)
    assert shares["test"] == pytest.approx(0.15, abs=0.01)


def test_balance_guard_rejects_a_skewed_split(settings: MLSettings) -> None:
    frame = assign_splits(_singleton_heavy_frame(), settings)
    skewed = frame.copy()
    skewed.loc[skewed["split"] == "val", "label"] = 1  # val becomes 100% phishing
    with pytest.raises(SplitImbalanceError, match="val is 100"):
        assert_balanced_splits(skewed, MLSettings())


def test_balance_guard_rejects_a_wrongly_sized_split(settings: MLSettings) -> None:
    frame = assign_splits(_singleton_heavy_frame(), settings)
    resized = frame.copy()
    resized.loc[resized["split"] == "test", "split"] = "val"  # val now ~30% of rows
    with pytest.raises(SplitImbalanceError, match="val holds"):
        assert_balanced_splits(resized, MLSettings())


def test_summary_counts_add_up(split_frame: pd.DataFrame) -> None:
    summaries = summarize_splits(split_frame)
    assert sum(s.rows for s in summaries.values()) == len(split_frame)
    assert sum(s.phishing for s in summaries.values()) == int(split_frame["label"].sum())
    for summary in summaries.values():
        assert summary.rows == summary.phishing + summary.legitimate
