from __future__ import annotations

from fastapi import APIRouter

from app.api.deps import CurrentUser
from app.services import ml_service

router = APIRouter(prefix="/models", tags=["models"])


@router.get("/current")
async def current_model(user: CurrentUser) -> dict[str, object]:
    return ml_service.current_model_info()
