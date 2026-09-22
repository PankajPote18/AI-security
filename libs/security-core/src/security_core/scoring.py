"""Deterministic risk scoring: the ML probability and indicator severities are combined by a
fixed, unit-tested formula, never by an LLM. Stage 3's LLM explains this score; it cannot change
it - that contract is what makes the score defensible.
"""

from __future__ import annotations

from dataclasses import dataclass

from security_core.indicators import Indicator

# Points added per indicator severity, nudging the ML-probability-derived base score.
_SEVERITY_POINTS: dict[str, float] = {"info": 0, "low": 3, "medium": 6, "high": 10}
_MAX_INDICATOR_POINTS = 30.0  # caps how much indicators alone can move the score
_ML_WEIGHT = 0.8  # the evaluated model remains the dominant signal; indicators corroborate it

LOW_THRESHOLD = 34.0
HIGH_THRESHOLD = 67.0


@dataclass(frozen=True)
class ScoringResult:
    risk_score: float  # 0-100
    risk_level: str  # "low" | "medium" | "high"
    classification: str  # "likely_legitimate" | "suspicious" | "likely_phishing"


def _indicator_points(indicators: list[Indicator]) -> float:
    return min(
        sum(_SEVERITY_POINTS.get(i.severity, 0.0) for i in indicators), _MAX_INDICATOR_POINTS
    )


def score(ml_probability: float, indicators: list[Indicator]) -> ScoringResult:
    if not 0.0 <= ml_probability <= 1.0:
        raise ValueError(f"ml_probability must be in [0, 1], got {ml_probability}")

    base = ml_probability * 100
    risk_score = min(100.0, base * _ML_WEIGHT + _indicator_points(indicators))

    if risk_score < LOW_THRESHOLD:
        level, classification = "low", "likely_legitimate"
    elif risk_score < HIGH_THRESHOLD:
        level, classification = "medium", "suspicious"
    else:
        level, classification = "high", "likely_phishing"

    return ScoringResult(
        risk_score=round(risk_score, 1), risk_level=level, classification=classification
    )
