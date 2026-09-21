from __future__ import annotations

import uuid

from sqlalchemy import ForeignKey, String
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column

from app.db.base import Base
from app.models._types import TimestampMixin, UuidPrimaryKeyMixin


class Feedback(UuidPrimaryKeyMixin, TimestampMixin, Base):
    __tablename__ = "feedback"

    analysis_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("analyses.id", ondelete="CASCADE"), index=True
    )
    user_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("users.id"), index=True
    )

    verdict: Mapped[str] = mapped_column(String(16))  # "agree" | "disagree"
    comment: Mapped[str | None] = mapped_column(String(2000), nullable=True)
