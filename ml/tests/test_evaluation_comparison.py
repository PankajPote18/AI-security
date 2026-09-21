from dataclasses import replace

import pandas as pd
import pytest
from sklearn.linear_model import LogisticRegression

from copilot_ml.evaluation.comparison import evaluate_candidate, rank, select_champion
from copilot_ml.features.vectorize import extract_feature_frame, select_view
from copilot_ml.training.pipeline import build_pipeline

_URLS = ["https://a.com/", "https://b.com/", "http://185.220.1.7/login", "https://bit.ly/x"] * 5
_LABELS = pd.Series([0, 0, 1, 1] * 5)


def _fit_and_evaluate(view: str, model_name: str = "logistic_regression") -> object:
    features = select_view(extract_feature_frame(_URLS), view)
    pipeline = build_pipeline(LogisticRegression(max_iter=200), view)
    pipeline.fit(features, _LABELS)
    return evaluate_candidate(model_name, view, pipeline, features, _LABELS, fit_seconds=0.1)


def test_evaluate_candidate_reports_sane_fields() -> None:
    result = _fit_and_evaluate("host")
    assert result.model_name == "logistic_regression"
    assert result.view == "host"
    assert result.artifact_size_bytes > 0
    assert result.predict_seconds >= 0.0
    assert 0.0 <= result.metrics.pr_auc <= 1.0


def test_rank_orders_by_pr_auc_descending() -> None:
    base = _fit_and_evaluate("host")
    better = replace(base, metrics=replace(base.metrics, pr_auc=1.0))
    worse = replace(base, metrics=replace(base.metrics, pr_auc=0.1))

    ranked = rank([worse, better])
    assert [r.metrics.pr_auc for r in ranked] == [1.0, 0.1]


def test_rank_tiebreaks_on_brier_then_latency_then_size() -> None:
    base = _fit_and_evaluate("host")
    tied_pr_auc = replace(base.metrics, pr_auc=0.9)

    lower_brier = replace(base, metrics=replace(tied_pr_auc, brier=0.05))
    higher_brier = replace(base, metrics=replace(tied_pr_auc, brier=0.20))

    ranked = rank([higher_brier, lower_brier])
    assert ranked[0] is lower_brier


def test_select_champion_only_considers_the_host_view() -> None:
    host_result = _fit_and_evaluate("host")
    full_result = _fit_and_evaluate("full")
    # Give the full-view candidate an unbeatable score to prove it is still excluded.
    full_result = replace(full_result, metrics=replace(full_result.metrics, pr_auc=1.0))

    champion = select_champion([host_result, full_result])
    assert champion.view == "host"


def test_select_champion_raises_if_no_host_view_candidate() -> None:
    only_full = _fit_and_evaluate("full")
    with pytest.raises(ValueError, match="host"):
        select_champion([only_full])
