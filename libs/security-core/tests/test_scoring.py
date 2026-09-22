import pytest
from app.services.scoring_service import HIGH_THRESHOLD, LOW_THRESHOLD, score

from security_core.indicators import Indicator


def _indicator(severity: str) -> Indicator:
    return Indicator(code="x", severity=severity, title="x", description="x", mitre_technique=None)


def test_zero_probability_no_indicators_is_low_risk() -> None:
    result = score(0.0, [])
    assert result.risk_score == 0.0
    assert result.risk_level == "low"
    assert result.classification == "likely_legitimate"


def test_certain_phishing_probability_is_high_risk() -> None:
    result = score(1.0, [])
    assert result.risk_score == 80.0  # 100 * 0.8 ML weight, no indicators
    assert result.risk_level == "high"
    assert result.classification == "likely_phishing"


def test_indicators_raise_the_score_on_top_of_the_ml_probability() -> None:
    without = score(0.3, [])
    with_high_indicator = score(0.3, [_indicator("high")])
    assert with_high_indicator.risk_score > without.risk_score
    assert with_high_indicator.risk_score == pytest.approx(without.risk_score + 10)


def test_indicator_points_are_capped() -> None:
    many_high = [_indicator("high") for _ in range(10)]  # far more than the cap
    result = score(0.0, many_high)
    assert result.risk_score == 30.0  # capped at _MAX_INDICATOR_POINTS


def test_score_never_exceeds_100() -> None:
    result = score(1.0, [_indicator("high") for _ in range(10)])
    assert result.risk_score == 100.0


@pytest.mark.parametrize("bad_probability", [-0.01, 1.01, 2.0, -1.0])
def test_out_of_range_probability_is_rejected(bad_probability: float) -> None:
    with pytest.raises(ValueError, match="probability"):
        score(bad_probability, [])


def test_thresholds_are_consistent_with_the_documented_levels() -> None:
    just_below_low = score((LOW_THRESHOLD - 0.1) / 100 / 0.8, [])
    just_at_high = score(HIGH_THRESHOLD / 100 / 0.8, [])
    assert just_below_low.risk_level == "low"
    assert just_at_high.risk_level == "high"


def test_unknown_severity_contributes_zero_points_rather_than_raising() -> None:
    weird = Indicator(
        code="x", severity="not_a_real_severity", title="x", description="x", mitre_technique=None
    )  # type: ignore[arg-type]
    result = score(0.0, [weird])
    assert result.risk_score == 0.0
