from __future__ import annotations

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.url import Url


async def get_by_sha256(db: AsyncSession, sha256: str) -> Url | None:
    result = await db.execute(select(Url).where(Url.sha256 == sha256))
    return result.scalar_one_or_none()


async def get_or_create(db: AsyncSession, *, normalized: str, sha256: str) -> Url:
    existing = await get_by_sha256(db, sha256)
    if existing is not None:
        return existing
    url = Url(normalized=normalized, sha256=sha256)
    db.add(url)
    await db.flush()
    return url
