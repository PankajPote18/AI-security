from __future__ import annotations

from fastapi import APIRouter, status
from fastapi.responses import JSONResponse

from app.services import ml_service

router = APIRouter(prefix="/health", tags=["health"])


@router.get("/live")
async def live() -> dict[str, str]:
    return {"status": "ok"}


@router.get("/ready")
async def ready() -> JSONResponse:
    try:
        ml_service.preload()
    except Exception as error:
        return JSONResponse(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            content={"status": "not_ready", "detail": str(error)},
        )
    return JSONResponse(content={"status": "ok"})
