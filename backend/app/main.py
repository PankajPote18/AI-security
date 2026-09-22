"""App factory. Kept to wiring only - no business logic lives here."""

from __future__ import annotations

import logging
from collections.abc import AsyncIterator
from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from slowapi import _rate_limit_exceeded_handler
from slowapi.errors import RateLimitExceeded
from slowapi.middleware import SlowAPIASGIMiddleware

from app.api.v1.health import router as health_router
from app.api.v1.router import router as v1_router
from app.core.config import get_settings
from app.core.errors import register_exception_handlers
from app.core.logging import RequestIdMiddleware, configure_logging
from app.core.rate_limit import limiter
from app.services import knowledge_service, ml_service

logger = logging.getLogger("app.startup")


@asynccontextmanager
async def lifespan(app: FastAPI) -> AsyncIterator[None]:
    del app  # unused: the app instance itself needs no setup here
    ml_service.preload()  # fail fast at startup: the ML model is required for /analyze/url

    try:
        # The knowledge base is Stage 3 enrichment (report generation); its absence must not
        # prevent the rest of the API from starting.
        result = knowledge_service.reingest()
        logger.info("Knowledge base indexed: %s", result)
    except Exception:
        logger.exception(
            "Knowledge base ingestion failed at startup; report generation will degrade"
        )

    yield


def create_app() -> FastAPI:
    configure_logging()
    settings = get_settings()

    app = FastAPI(title="AI Security Copilot API", version="0.1.0", lifespan=lifespan)

    app.state.limiter = limiter
    # slowapi's handler type is narrower than Starlette's stub expects.
    app.add_exception_handler(RateLimitExceeded, _rate_limit_exceeded_handler)  # type: ignore[arg-type]
    app.add_middleware(SlowAPIASGIMiddleware)
    app.add_middleware(RequestIdMiddleware)
    app.add_middleware(
        CORSMiddleware,
        allow_origins=settings.cors_origins,
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )

    register_exception_handlers(app)

    app.include_router(health_router)
    app.include_router(v1_router)

    return app


app = create_app()
