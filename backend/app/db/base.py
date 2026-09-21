"""Declarative base every ORM model inherits from. Alembic's `env.py` imports `Base.metadata`
plus every model module (via `app.models`) so autogenerate sees the full schema.
"""

from __future__ import annotations

from sqlalchemy.orm import DeclarativeBase


class Base(DeclarativeBase):
    pass
