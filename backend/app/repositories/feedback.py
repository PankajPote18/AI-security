from __future__ import annotations

import uuid

from sqlalchemy.ext.asyncio import AsyncSession

from app.models.feedback import Feedback


async def create(
    db: AsyncSession,
    *,
    analysis_id: uuid.UUID,
    user_id: uuid.UUID,
    verdict: str,
    comment: str | None,
) -> Feedback:
    feedback = Feedback(analysis_id=analysis_id, user_id=user_id, verdict=verdict, comment=comment)
    db.add(feedback)
    await db.flush()
    return feedback
