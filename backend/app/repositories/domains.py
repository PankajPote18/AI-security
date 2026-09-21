from __future__ import annotations

import uuid
from datetime import datetime

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.domain import Domain


async def get_by_registered_domain(db: AsyncSession, registered_domain: str) -> Domain | None:
    result = await db.execute(select(Domain).where(Domain.registered_domain == registered_domain))
    return result.scalar_one_or_none()


async def get_by_id(db: AsyncSession, domain_id: uuid.UUID) -> Domain | None:
    return await db.get(Domain, domain_id)


async def upsert_snapshot(
    db: AsyncSession,
    *,
    registered_domain: str,
    dns_snapshot: dict,
    rdap_snapshot: dict,
    domain_created_at: datetime | None,
    refreshed_at: datetime,
) -> Domain:
    """Refresh the durable DNS/RDAP snapshot for a domain, creating the row on first sight."""
    existing = await get_by_registered_domain(db, registered_domain)
    if existing is not None:
        existing.dns_snapshot = dns_snapshot
        existing.rdap_snapshot = rdap_snapshot
        existing.domain_created_at = domain_created_at
        existing.refreshed_at = refreshed_at
        await db.flush()
        return existing

    domain = Domain(
        registered_domain=registered_domain,
        dns_snapshot=dns_snapshot,
        rdap_snapshot=rdap_snapshot,
        domain_created_at=domain_created_at,
        refreshed_at=refreshed_at,
    )
    db.add(domain)
    await db.flush()
    return domain
