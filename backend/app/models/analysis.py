from __future__ import annotations

import uuid
from datetime import datetime

from sqlalchemy import JSON, Boolean, DateTime, Float, ForeignKey, String
from sqlalchemy.dialects.postgresql import JSONB, UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db.base import Base
from app.models._types import TimestampMixin, UuidPrimaryKeyMixin
from app.models.url import Url

# Kept as plain strings (validated by the Pydantic schema / scoring_service), not a Postgres
# native enum, so adding a status or risk level later is a plain data change, not a migration
# that touches an enum type.
AnalysisStatus = str  # "pending" | "running" | "completed" | "failed"
RiskLevel = str  # "low" | "medium" | "high"


class Analysis(UuidPrimaryKeyMixin, TimestampMixin, Base):
    __tablename__ = "analyses"

    user_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("users.id", ondelete="CASCADE"), index=True
    )
    url_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), ForeignKey("urls.id"), index=True)
    domain_id: Mapped[uuid.UUID | None] = mapped_column(
        UUID(as_uuid=True), ForeignKey("domains.id"), nullable=True
    )
    url: Mapped[Url] = relationship(lazy="raise")  # loaded explicitly via selectinload only

    status: Mapped[str] = mapped_column(String(16), default="pending")
    mode: Mapped[str] = mapped_column(
        String(16), default="standard"
    )  # "standard" | "deep" (Stage 4)
    # One entry per pipeline step ({"step": "ml", "status": "done", "ms": 12.3, ...}), so the
    # frontend can show progress and so a failure is traceable to exactly one step.
    steps: Mapped[list] = mapped_column(JSONB().with_variant(JSON(), "sqlite"), default=list)

    risk_score: Mapped[float | None] = mapped_column(Float, nullable=True)  # 0-100
    risk_level: Mapped[str | None] = mapped_column(String(16), nullable=True)
    classification: Mapped[str | None] = mapped_column(String(32), nullable=True)
    indicators: Mapped[list] = mapped_column(JSONB().with_variant(JSON(), "sqlite"), default=list)

    degraded: Mapped[bool] = mapped_column(Boolean, default=False)
    error: Mapped[str | None] = mapped_column(String(1024), nullable=True)
    completed_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
