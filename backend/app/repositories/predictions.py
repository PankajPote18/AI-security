from __future__ import annotations

import uuid
from typing import Any

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.prediction import Prediction


async def create(
    db: AsyncSession,
    *,
    analysis_id: uuid.UUID,
    model_name: str,
    feature_schema_version: str,
    artifact_sha256: str,
    probability: float,
    threshold: float,
    label: int,
    top_contributions: list[dict[str, Any]],
    latency_ms: float,
) -> Prediction:
    prediction = Prediction(
        analysis_id=analysis_id,
        model_name=model_name,
        feature_schema_version=feature_schema_version,
        artifact_sha256=artifact_sha256,
        probability=probability,
        threshold=threshold,
        label=label,
        top_contributions=top_contributions,
        latency_ms=latency_ms,
    )
    db.add(prediction)
    await db.flush()
    return prediction


async def get_by_analysis_id(db: AsyncSession, analysis_id: uuid.UUID) -> Prediction | None:
    result = await db.execute(select(Prediction).where(Prediction.analysis_id == analysis_id))
    return result.scalar_one_or_none()
