from __future__ import annotations

import uuid
from datetime import datetime

from pydantic import BaseModel, ConfigDict, Field

from app.schemas.evidence import DomainInfoOut, IndicatorOut, MlAnalysisOut


class AnalyzeRequest(BaseModel):
    url: str = Field(min_length=1, max_length=2048)


class AnalysisStepOut(BaseModel):
    step: str
    status: str
    ms: float | None = None
    error: str | None = None


class AnalysisSummaryOut(BaseModel):
    """One row of `GET /analyses` - deliberately excludes the heavier evidence fields."""

    model_config = ConfigDict(from_attributes=True)

    id: uuid.UUID
    url: str
    status: str
    risk_score: float | None
    risk_level: str | None
    classification: str | None
    created_at: datetime


class AnalysisOut(BaseModel):
    """`GET /analyses/{id}` and the response of `POST /analyze/url`.

    AI explanation, retrieved sources and threat-intelligence fields are declared now (as
    always-null in Stage 2) so the response shape does not change when Stage 3/4 fill them in.
    """

    id: uuid.UUID
    url: str
    status: str
    mode: str
    steps: list[AnalysisStepOut]

    risk_score: float | None
    risk_level: str | None
    classification: str | None
    degraded: bool
    error: str | None

    ml_analysis: MlAnalysisOut | None
    indicators: list[IndicatorOut]
    domain_info: DomainInfoOut | None
    threat_intelligence: list[dict] | None = None  # Stage 4
    ai_explanation: str | None = None  # Stage 3
    sources: list[dict] | None = None  # Stage 3

    created_at: datetime
    completed_at: datetime | None


class FeedbackRequest(BaseModel):
    verdict: str = Field(pattern="^(agree|disagree)$")
    comment: str | None = Field(default=None, max_length=2000)


class FeedbackOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: uuid.UUID
    analysis_id: uuid.UUID
    verdict: str
    comment: str | None
