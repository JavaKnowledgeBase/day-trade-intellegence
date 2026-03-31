"""Request middleware that assigns a correlation identifier to every API call."""

import logging
import time
import uuid

from starlette.middleware.base import BaseHTTPMiddleware
from starlette.requests import Request
from starlette.responses import Response

logger = logging.getLogger(__name__)


class RequestContextMiddleware(BaseHTTPMiddleware):
    """Attach a request ID and log request lifecycle timing for enterprise observability."""

    async def dispatch(self, request: Request, call_next) -> Response:
        """Generate a request ID, log start/end events, and return the ID in the response headers."""
        request_id = request.headers.get("X-Request-ID", str(uuid.uuid4()))
        start_time = time.perf_counter()
        request.state.request_id = request_id

        logger.info("HTTP request started", extra={"request_id": request_id, "method": request.method, "path": request.url.path})
        response = await call_next(request)
        duration_ms = round((time.perf_counter() - start_time) * 1000, 2)
        response.headers["X-Request-ID"] = request_id
        logger.info("HTTP request completed", extra={"request_id": request_id, "method": request.method, "path": request.url.path, "status_code": response.status_code, "duration_ms": duration_ms})
        return response
