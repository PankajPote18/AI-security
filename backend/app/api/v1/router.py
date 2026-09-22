from __future__ import annotations

from fastapi import APIRouter

from app.api.v1 import analyses, auth, knowledge, models

router = APIRouter(prefix="/api/v1")
router.include_router(auth.router)
router.include_router(analyses.router)
router.include_router(models.router)
router.include_router(knowledge.router)
