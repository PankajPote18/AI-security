"""Every read here is scoped to a `user_id` (authorisation, not just a convenience filter): a
user must never be able to fetch another user's analysis by guessing its id.
"""

from __future__ import annotations

import uuid

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from app.models.analysis import Analysis


async def create(
    db: AsyncSession, *, user_id: uuid.UUID, url_id: uuid.UUID, mode: str = "standard"
) -> Analysis:
    analysis = Analysis(user_id=user_id, url_id=url_id, mode=mode, status="pending")
    db.add(analysis)
    await db.flush()
    return analysis


async def get_for_user(
    db: AsyncSession, *, analysis_id: uuid.UUID, user_id: uuid.UUID
) -> Analysis | None:
    result = await db.execute(
        select(Analysis)
        .where(Analysis.id == analysis_id, Analysis.user_id == user_id)
        .options(selectinload(Analysis.url))
    )
    return result.scalar_one_or_none()


async def list_for_user(
    db: AsyncSession, *, user_id: uuid.UUID, limit: int = 20, offset: int = 0
) -> list[Analysis]:
    result = await db.execute(
        select(Analysis)
        .where(Analysis.user_id == user_id)
        .order_by(Analysis.created_at.desc())
        .limit(limit)
        .offset(offset)
        .options(selectinload(Analysis.url))
    )
    return list(result.scalars())
