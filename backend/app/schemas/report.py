from __future__ import annotations

import uuid
from datetime import datetime

from pydantic import BaseModel, ConfigDict


class IndicatorExplanationOut(BaseModel):
    indicator_code: str
    explanation: str
    source_numbers: list[int]


class SourceOut(BaseModel):
    chunk_id: str
    doc_id: str | None
    title: str | None
    source_name: str | None
    source_url: str | None
    topic: str | None
    score: float


class SecurityReportOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: uuid.UUID
    analysis_id: uuid.UUID
    status: str  # "completed" | "failed"
    provider: str
    model_name: str
    prompt_version: str

    summary: str | None
    indicator_explanations: list[IndicatorExplanationOut]
    recommendations: list[str]
    sources: list[SourceOut]
    error: str | None

    latency_ms: float
    created_at: datetime
