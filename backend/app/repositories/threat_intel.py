from __future__ import annotations

import uuid
from datetime import datetime

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.threat_intel import ThreatIntelLookup


async def get_by_url_and_provider(
    db: AsyncSession, *, url_id: uuid.UUID, provider: str
) -> ThreatIntelLookup | None:
    result = await db.execute(
        select(ThreatIntelLookup).where(
            ThreatIntelLookup.url_id == url_id, ThreatIntelLookup.provider == provider
        )
    )
    return result.scalar_one_or_none()


async def list_by_url(db: AsyncSession, url_id: uuid.UUID) -> list[ThreatIntelLookup]:
    result = await db.execute(
        select(ThreatIntelLookup)
        .where(ThreatIntelLookup.url_id == url_id)
        .order_by(ThreatIntelLookup.provider)
    )
    return list(result.scalars())


async def upsert(
    db: AsyncSession,
    *,
    url_id: uuid.UUID,
    provider: str,
    status: str,
    threat_type: str | None,
    tags: list[str],
    reference_url: str | None,
    error: str | None,
    fetched_at: datetime,
) -> ThreatIntelLookup:
    """Refresh the durable verdict for one (url, provider) pair, creating the row on first sight."""
    existing = await get_by_url_and_provider(db, url_id=url_id, provider=provider)
    if existing is not None:
        existing.status = status
        existing.threat_type = threat_type
        existing.tags = tags
        existing.reference_url = reference_url
        existing.error = error
        existing.fetched_at = fetched_at
        await db.flush()
        return existing

    lookup = ThreatIntelLookup(
        url_id=url_id,
        provider=provider,
        status=status,
        threat_type=threat_type,
        tags=tags,
        reference_url=reference_url,
        error=error,
        fetched_at=fetched_at,
    )
    db.add(lookup)
    await db.flush()
    return lookup
