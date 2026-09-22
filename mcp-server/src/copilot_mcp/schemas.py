"""Structured tool outputs. Deliberately not shared with `backend/app/schemas` - this package
must not import the backend (apps never import each other), and these shapes are the MCP
protocol's structured-content contract, not the API's, so they are free to diverge from it.
"""

from __future__ import annotations

from pydantic import BaseModel, Field


class IndicatorOut(BaseModel):
    code: str
    severity: str
    title: str
    description: str
    mitre_technique: str | None = None


class UrlAnalysisOut(BaseModel):
    url: str
    risk_score: float
    risk_level: str
    classification: str
    ml_probability: float
    ml_model_name: str
    indicators: list[IndicatorOut] = Field(default_factory=list)


class DnsRecordOut(BaseModel):
    record_type: str
    values: list[str] = Field(default_factory=list)
    error: str | None = None


class DnsLookupOut(BaseModel):
    host: str
    resolved: bool
    records: list[DnsRecordOut] = Field(default_factory=list)


class DomainInfoOut(BaseModel):
    domain: str
    found: bool
    registrar: str | None = None
    created_at: str | None = None
    age_days: int | None = None
    status: list[str] = Field(default_factory=list)
    error: str | None = None


class ThreatIntelOut(BaseModel):
    provider: str
    status: str  # "listed" | "not_listed" | "unavailable"
    threat_type: str | None = None
    tags: list[str] = Field(default_factory=list)
    reference_url: str | None = None
    error: str | None = None


class KnowledgeSourceOut(BaseModel):
    chunk_id: str
    doc_id: str | None = None
    title: str | None = None
    source_name: str | None = None
    source_url: str | None = None
    topic: str | None = None
    score: float
    text: str
