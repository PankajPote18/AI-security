"""Rebase precision (PPV) from this dataset's inflated phishing prevalence to a realistic one.

This dataset is ~43% phishing; real URL traffic is nowhere close (well under a few percent).
Precision computed directly on this data is therefore optimistic. Recall and the false-positive
rate transfer across prevalence (they are conditioned on the true class), so precision at any
assumed real-world prevalence can be rebased from them via Bayes' rule.
"""

from __future__ import annotations

from dataclasses import dataclass

from copilot_ml.evaluation.metrics import ClassificationMetrics

REALISTIC_PREVALENCE = 0.01  # a conservative estimate of phishing share of all URL traffic


@dataclass(frozen=True)
class PrevalenceAdjustedPrecision:
    assumed_prevalence: float
    recall: float
    false_positive_rate: float
    precision_at_prevalence: float


def false_positive_rate(fp: int, tn: int) -> float:
    denom = fp + tn
    return fp / denom if denom else 0.0


def precision_at_prevalence(recall: float, fpr: float, prevalence: float) -> float:
    true_positive_mass = recall * prevalence
    false_positive_mass = fpr * (1 - prevalence)
    denom = true_positive_mass + false_positive_mass
    return true_positive_mass / denom if denom else 0.0


def rebase_precision(
    metrics: ClassificationMetrics, prevalence: float = REALISTIC_PREVALENCE
) -> PrevalenceAdjustedPrecision:
    fpr = false_positive_rate(metrics.fp, metrics.tn)
    precision = precision_at_prevalence(metrics.recall, fpr, prevalence)
    return PrevalenceAdjustedPrecision(prevalence, metrics.recall, fpr, precision)
