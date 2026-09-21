from __future__ import annotations

import uuid

from fastapi import APIRouter, HTTPException, Request, status

from app.api.deps import CurrentUser, DbSession
from app.core.config import get_settings
from app.core.rate_limit import limiter
from app.repositories import analyses as analyses_repo
from app.repositories import feedback as feedback_repo
from app.schemas.analysis import (
    AnalysisOut,
    AnalysisSummaryOut,
    AnalyzeRequest,
    FeedbackOut,
    FeedbackRequest,
)
from app.services import analysis_service
from app.services.analysis_service import AnalysisNotFoundError

router = APIRouter(tags=["analyses"])


@router.post("/analyze/url", response_model=AnalysisOut)
@limiter.limit(get_settings().rate_limit_analyze)
async def analyze_url(
    request: Request, payload: AnalyzeRequest, user: CurrentUser, db: DbSession
) -> AnalysisOut:
    try:
        return await analysis_service.run_analysis(db, user_id=user.id, raw_url=payload.url)
    except ValueError as error:
        raise HTTPException(status.HTTP_422_UNPROCESSABLE_CONTENT, str(error)) from error


@router.get("/analyses", response_model=list[AnalysisSummaryOut])
async def list_analyses(
    user: CurrentUser, db: DbSession, limit: int = 20, offset: int = 0
) -> list[AnalysisSummaryOut]:
    rows = await analyses_repo.list_for_user(
        db, user_id=user.id, limit=min(max(limit, 1), 100), offset=max(offset, 0)
    )
    return [
        AnalysisSummaryOut(
            id=row.id,
            url=row.url.normalized,
            status=row.status,
            risk_score=row.risk_score,
            risk_level=row.risk_level,
            classification=row.classification,
            created_at=row.created_at,
        )
        for row in rows
    ]


@router.get("/analyses/{analysis_id}", response_model=AnalysisOut)
async def get_analysis(analysis_id: uuid.UUID, user: CurrentUser, db: DbSession) -> AnalysisOut:
    try:
        return await analysis_service.get_analysis(db, analysis_id=analysis_id, user_id=user.id)
    except AnalysisNotFoundError as error:
        raise HTTPException(status.HTTP_404_NOT_FOUND, "Analysis not found") from error


@router.post(
    "/analyses/{analysis_id}/feedback",
    response_model=FeedbackOut,
    status_code=status.HTTP_201_CREATED,
)
async def submit_feedback(
    analysis_id: uuid.UUID, payload: FeedbackRequest, user: CurrentUser, db: DbSession
) -> FeedbackOut:
    try:
        await analysis_service.get_analysis(db, analysis_id=analysis_id, user_id=user.id)
    except AnalysisNotFoundError as error:
        raise HTTPException(status.HTTP_404_NOT_FOUND, "Analysis not found") from error

    row = await feedback_repo.create(
        db,
        analysis_id=analysis_id,
        user_id=user.id,
        verdict=payload.verdict,
        comment=payload.comment,
    )
    await db.commit()
    return FeedbackOut.model_validate(row)
