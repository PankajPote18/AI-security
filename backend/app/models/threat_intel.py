from __future__ import annotations

import uuid
from datetime import datetime

from sqlalchemy import JSON, DateTime, ForeignKey, String, UniqueConstraint
from sqlalchemy.dialects.postgresql import JSONB, UUID
from sqlalchemy.orm import Mapped, mapped_column

from app.db.base import Base
from app.models._types import TimestampMixin, UuidPrimaryKeyMixin


class ThreatIntelLookup(UuidPrimaryKeyMixin, TimestampMixin, Base):
    """A durable, per-(url, provider) threat-intelligence verdict. Doubles as a cache: `fetched_at`
    lets `security_analysis_service` skip a re-lookup that is still fresh, the same role `Domain`
    plays for DNS/RDAP."""

    __tablename__ = "threat_intel_lookups"
    __table_args__ = (UniqueConstraint("url_id", "provider", name="uq_threat_intel_url_provider"),)

    url_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("urls.id", ondelete="CASCADE"), index=True
    )
    provider: Mapped[str] = mapped_column(String(32))
    status: Mapped[str] = mapped_column(String(16))  # "listed" | "not_listed" | "unavailable"
    threat_type: Mapped[str | None] = mapped_column(String(64), nullable=True)
    tags: Mapped[list] = mapped_column(JSONB().with_variant(JSON(), "sqlite"), default=list)
    reference_url: Mapped[str | None] = mapped_column(String(512), nullable=True)
    error: Mapped[str | None] = mapped_column(String(256), nullable=True)
    fetched_at: Mapped[datetime] = mapped_column(DateTime(timezone=True))
