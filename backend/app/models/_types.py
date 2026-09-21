"""Shared column type/mixin helpers so every model declares primary keys and timestamps the
same way instead of repeating the boilerplate (and risking it drifting) in each one."""

from __future__ import annotations

import uuid
from datetime import datetime

from sqlalchemy import DateTime, text
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column
from sqlalchemy.sql import func


class UuidPrimaryKeyMixin:
    """UUID rather than a sequential integer, so IDs are not enumerable in a security product."""

    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), primary_key=True, server_default=text("gen_random_uuid()")
    )


class TimestampMixin:
    # Every timestamp column in this app is timezone-aware (UTC): application code writes
    # tz-aware `datetime.now(UTC)` values, and asyncpg rejects those against a naive column.
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())
