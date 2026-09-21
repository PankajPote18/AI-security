"""Structured-enough logging: every log line carries a request id, and query strings (which may
contain the analysed URL's original text or other user data) are never logged verbatim.
"""

from __future__ import annotations

import logging
import re
import uuid
from collections.abc import Awaitable, Callable

from starlette.middleware.base import BaseHTTPMiddleware
from starlette.requests import Request
from starlette.responses import Response

REQUEST_ID_HEADER = "X-Request-ID"
_QUERY_REDACTED = re.compile(r"\?.*$")


def configure_logging(level: int = logging.INFO) -> None:
    logging.basicConfig(
        level=level, format="%(asctime)s %(levelname)-8s %(name)s [%(request_id)s] %(message)s"
    )
    logging.getLogger().addFilter(_DefaultRequestIdFilter())


class _DefaultRequestIdFilter(logging.Filter):
    def filter(self, record: logging.LogRecord) -> bool:
        if not hasattr(record, "request_id"):
            record.request_id = "-"
        return True


class RequestIdMiddleware(BaseHTTPMiddleware):
    async def dispatch(
        self, request: Request, call_next: Callable[[Request], Awaitable[Response]]
    ) -> Response:
        request_id = request.headers.get(REQUEST_ID_HEADER) or str(uuid.uuid4())
        request.state.request_id = request_id

        logger = logging.getLogger("app.request")
        path = _QUERY_REDACTED.sub("", str(request.url.path))
        logger.info("%s %s", request.method, path, extra={"request_id": request_id})

        response = await call_next(request)
        response.headers[REQUEST_ID_HEADER] = request_id
        return response
