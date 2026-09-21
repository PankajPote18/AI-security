from __future__ import annotations

import uuid

from sqlalchemy import JSON, Float, ForeignKey, String
from sqlalchemy.dialects.postgresql import JSONB, UUID
from sqlalchemy.orm import Mapped, mapped_column

from app.db.base import Base
from app.models._types import TimestampMixin, UuidPrimaryKeyMixin


class Prediction(UuidPrimaryKeyMixin, TimestampMixin, Base):
    """The ML model's contribution to one analysis, kept separate from `Analysis` so the model
    identity and feature-schema version that produced a score are always reconstructable."""

    __tablename__ = "predictions"

    analysis_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("analyses.id", ondelete="CASCADE"), unique=True, index=True
    )

    model_name: Mapped[str] = mapped_column(String(64))
    feature_schema_version: Mapped[str] = mapped_column(String(16))
    artifact_sha256: Mapped[str] = mapped_column(String(64))

    probability: Mapped[float] = mapped_column(Float)
    threshold: Mapped[float] = mapped_column(Float)
    label: Mapped[int] = mapped_column()  # 1 = phishing, 0 = legitimate

    top_contributions: Mapped[list] = mapped_column(
        JSONB().with_variant(JSON(), "sqlite"), default=list
    )
    latency_ms: Mapped[float] = mapped_column(Float)
