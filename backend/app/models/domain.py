from __future__ import annotations

from datetime import datetime

from sqlalchemy import JSON, DateTime, String
from sqlalchemy.dialects.postgresql import JSONB
from sqlalchemy.orm import Mapped, mapped_column

from app.db.base import Base
from app.models._types import TimestampMixin, UuidPrimaryKeyMixin


class Domain(UuidPrimaryKeyMixin, TimestampMixin, Base):
    """A durable, slowly-changing snapshot of a registered domain's DNS/RDAP facts. Doubles as
    a cache: `refreshed_at` lets `security_analysis_service` skip a re-lookup that is still
    fresh rather than hitting DNS/RDAP on every analysis of the same domain."""

    __tablename__ = "domains"

    registered_domain: Mapped[str] = mapped_column(String(253), unique=True, index=True)
    dns_snapshot: Mapped[dict] = mapped_column(JSONB().with_variant(JSON(), "sqlite"), default=dict)
    rdap_snapshot: Mapped[dict] = mapped_column(
        JSONB().with_variant(JSON(), "sqlite"), default=dict
    )
    domain_created_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))
    refreshed_at: Mapped[datetime] = mapped_column(DateTime(timezone=True))
