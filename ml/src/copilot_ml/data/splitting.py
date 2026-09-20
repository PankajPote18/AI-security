"""Train/validation/test split that never separates a site across splits.

Sites (see `grouping`) are assigned whole to one of `n_folds` folds by a greedy, class-aware
procedure: largest sites first, each into the fold whose class mix stays closest to the target.
Folds are then mapped to splits (14/3/3 of 20 folds = 70/15/15).

This is the same idea as scikit-learn's StratifiedGroupKFold, implemented directly because that
class takes ~8 minutes on this dataset's ~200k sites (mostly single-URL) versus seconds here.
Correctness rests on two properties that are tested: every site lands in exactly one fold, and
per-split class ratios stay close to the overall ratio.
"""

from __future__ import annotations

from dataclasses import asdict, dataclass
from itertools import combinations

import numpy as np
import pandas as pd

from copilot_ml.config import SPLIT_NAMES, MLSettings


class SiteLeakageError(AssertionError):
    """At least one site appears in more than one split."""


class SplitImbalanceError(AssertionError):
    """A split's size or class ratio deviates from the target by more than the tolerance."""


@dataclass(frozen=True)
class SplitSummary:
    rows: int
    phishing: int
    legitimate: int
    sites: int

    @property
    def phishing_rate(self) -> float:
        return self.phishing / self.rows if self.rows else 0.0

    def as_dict(self) -> dict[str, int | float]:
        return {**asdict(self), "phishing_rate": round(self.phishing_rate, 6)}


def _assign_sites_to_folds(
    class_counts: np.ndarray, n_folds: int, rng: np.random.Generator
) -> np.ndarray:
    """Greedy class-aware assignment. `class_counts` is (n_sites, n_classes); returns fold ids."""
    n_sites = len(class_counts)
    # Largest sites first; ties broken by a seeded shuffle so the result is reproducible.
    order = np.lexsort((rng.permutation(n_sites), -class_counts.sum(axis=1)))
    target = np.maximum(class_counts.sum(axis=0) / n_folds, 1.0)  # per-fold, per-class

    load = np.zeros((n_folds, class_counts.shape[1]))
    fold_of_site = np.empty(n_sites, dtype=np.int64)
    for site in order:
        after = load + class_counts[site]
        # Change in each fold's squared deviation from target if this site were added to it:
        # the fold with the largest deficit (most negative change) wins.
        change = ((after - target) ** 2 - (load - target) ** 2) / target
        fold = int(np.argmin(change.sum(axis=1)))
        load[fold] = after[fold]
        fold_of_site[site] = fold
    return fold_of_site


def assign_splits(frame: pd.DataFrame, settings: MLSettings) -> pd.DataFrame:
    rng = np.random.default_rng(settings.seed)

    by_site = frame.groupby("site")["label"].agg(rows="size", phishing="sum")
    class_counts = np.column_stack(
        [(by_site["rows"] - by_site["phishing"]).to_numpy(), by_site["phishing"].to_numpy()]
    )
    fold_of_site = _assign_sites_to_folds(class_counts, settings.n_folds, rng)

    # Ties in the greedy step favour low fold ids, so shuffle which folds become which split.
    split_of_fold = np.array(
        [name for name in SPLIT_NAMES for _ in range(settings.split_folds[name])]
    )[rng.permutation(settings.n_folds)]
    split_of_site = pd.Series(split_of_fold[fold_of_site], index=by_site.index)

    assigned = frame.copy()
    assigned["split"] = assigned["site"].map(split_of_site)
    return assigned


def summarize_splits(frame: pd.DataFrame) -> dict[str, SplitSummary]:
    summaries: dict[str, SplitSummary] = {}
    for name in SPLIT_NAMES:
        part = frame[frame["split"] == name]
        phishing = int((part["label"] == 1).sum())
        summaries[name] = SplitSummary(
            rows=len(part),
            phishing=phishing,
            legitimate=len(part) - phishing,
            sites=int(part["site"].nunique()),
        )
    return summaries


def site_overlap(frame: pd.DataFrame) -> dict[str, int]:
    """Number of sites shared by each pair of splits. Must be zero for every pair."""
    sites = {name: set(frame.loc[frame["split"] == name, "site"]) for name in SPLIT_NAMES}
    return {f"{a}&{b}": len(sites[a] & sites[b]) for a, b in combinations(SPLIT_NAMES, 2)}


def assert_no_site_leakage(frame: pd.DataFrame) -> None:
    leaks = {pair: count for pair, count in site_overlap(frame).items() if count}
    if leaks:
        raise SiteLeakageError(f"Sites shared across splits: {leaks}")


def assert_balanced_splits(frame: pd.DataFrame, settings: MLSettings) -> None:
    """Fail the build rather than write splits whose size or class mix is visibly off."""
    overall_rate = float(frame["label"].mean())
    problems: list[str] = []
    for name, summary in summarize_splits(frame).items():
        target_share = settings.split_folds[name] / settings.n_folds
        share_gap = abs(summary.rows / len(frame) - target_share)
        rate_gap = abs(summary.phishing_rate - overall_rate)
        if share_gap > settings.max_share_gap:
            problems.append(f"{name} holds {summary.rows / len(frame):.1%} of rows")
        if rate_gap > settings.max_class_rate_gap:
            problems.append(
                f"{name} is {summary.phishing_rate:.1%} phishing (overall {overall_rate:.1%})"
            )
    if problems:
        raise SplitImbalanceError("Unbalanced split: " + "; ".join(problems))
