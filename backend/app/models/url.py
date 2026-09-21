from __future__ import annotations

from sqlalchemy import String
from sqlalchemy.orm import Mapped, mapped_column

from app.db.base import Base
from app.models._types import TimestampMixin, UuidPrimaryKeyMixin


class Url(UuidPrimaryKeyMixin, TimestampMixin, Base):
    """One row per distinct normalised URL ever submitted; `sha256` dedupes re-submissions."""

    __tablename__ = "urls"

    normalized: Mapped[str] = mapped_column(String(2048))
    sha256: Mapped[str] = mapped_column(String(64), unique=True, index=True)
