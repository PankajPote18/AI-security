"""The pieces of evidence that feed `scoring_service` and are shown to the user. Kept as a
separate module from `analysis.py` because these shapes are the contract the LLM (Stage 3) and
the MCP tools (Stage 4) will also produce/consume - they outlive any one API response shape.
"""

from __future__ import annotations

from datetime import datetime

from pydantic import BaseModel


class FeatureContributionOut(BaseModel):
    feature: str
    shap_value: float


class MlAnalysisOut(BaseModel):
    model_name: str
    probability: float
    threshold: float
    label: int  # 1 = phishing, 0 = legitimate
    top_contributions: list[FeatureContributionOut]
    latency_ms: float


class IndicatorOut(BaseModel):
    code: str
    severity: str
    title: str
    description: str
    mitre_technique: str | None = None


class DnsRecordOut(BaseModel):
    record_type: str
    values: list[str]
    error: str | None = None


class DomainInfoOut(BaseModel):
    registered_domain: str
    dns_records: list[DnsRecordOut]
    dns_resolved: bool
    registrar: str | None = None
    domain_created_at: datetime | None = None
    domain_age_days: int | None = None
    rdap_found: bool = False
    degraded: bool = False
