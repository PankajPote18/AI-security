from __future__ import annotations

import uuid

from sqlalchemy import JSON, Float, ForeignKey, Integer, String
from sqlalchemy.dialects.postgresql import JSONB, UUID
from sqlalchemy.orm import Mapped, mapped_column

from app.db.base import Base
from app.models._types import TimestampMixin, UuidPrimaryKeyMixin


class SecurityReport(UuidPrimaryKeyMixin, TimestampMixin, Base):
    """The LLM's explanation of an analysis's evidence. One per analysis (regenerating replaces
    it) - the report is derived, disposable content; the evidence it explains (`analyses`,
    `predictions`) is the durable record."""

    __tablename__ = "security_reports"

    analysis_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("analyses.id", ondelete="CASCADE"), unique=True, index=True
    )

    status: Mapped[str] = mapped_column(String(16))  # "completed" | "failed"
    provider: Mapped[str] = mapped_column(String(32))
    model_name: Mapped[str] = mapped_column(String(128))
    prompt_version: Mapped[str] = mapped_column(String(32))

    report: Mapped[dict | None] = mapped_column(
        JSONB().with_variant(JSON(), "sqlite"), nullable=True
    )
    sources: Mapped[list] = mapped_column(JSONB().with_variant(JSON(), "sqlite"), default=list)
    error: Mapped[str | None] = mapped_column(String(1024), nullable=True)

    prompt_tokens: Mapped[int | None] = mapped_column(Integer, nullable=True)
    completion_tokens: Mapped[int | None] = mapped_column(Integer, nullable=True)
    latency_ms: Mapped[float] = mapped_column(Float)
