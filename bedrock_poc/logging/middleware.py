"""FastAPI middleware for structured request/response logging."""

import logging
import time
from typing import Callable

from fastapi import Request, Response
from starlette.middleware.base import BaseHTTPMiddleware

from bedrock_poc.logging.correlation import get_correlation_id, set_correlation_id

logger = logging.getLogger(__name__)


class RequestLoggingMiddleware(BaseHTTPMiddleware):
    """Middleware for structured request/response logging with correlation IDs."""

    async def dispatch(self, request: Request, call_next: Callable) -> Response:
        """Log request and response details.

        Args:
            request: HTTP request
            call_next: Next middleware/handler

        Returns:
            HTTP response
        """
        # Extract or generate correlation ID
        correlation_id = request.headers.get("X-Correlation-ID")
        if not correlation_id:
            correlation_id = get_correlation_id()
        set_correlation_id(correlation_id)

        # Record request details
        start_time = time.time()
        method = request.method
        url = str(request.url)
        client_host = request.client.host if request.client else "unknown"

        logger.info(
            f"Request started: {method} {url}",
            extra={
                "extras": {
                    "method": method,
                    "path": request.url.path,
                    "client": client_host,
                    "correlation_id": correlation_id,
                }
            },
        )

        try:
            # Process request
            response = await call_next(request)

            # Calculate duration
            duration_ms = (time.time() - start_time) * 1000

            # Log response
            logger.info(
                f"Request completed: {method} {request.url.path} {response.status_code}",
                extra={
                    "extras": {
                        "method": method,
                        "path": request.url.path,
                        "status_code": response.status_code,
                        "duration_ms": duration_ms,
                        "client": client_host,
                        "correlation_id": correlation_id,
                    }
                },
            )

            # Add correlation ID to response headers
            response.headers["X-Correlation-ID"] = correlation_id

            return response

        except Exception as e:
            # Log error
            duration_ms = (time.time() - start_time) * 1000
            logger.error(
                f"Request failed: {method} {request.url.path}",
                exc_info=True,
                extra={
                    "extras": {
                        "method": method,
                        "path": request.url.path,
                        "duration_ms": duration_ms,
                        "client": client_host,
                        "error": str(e),
                        "correlation_id": correlation_id,
                    }
                },
            )
            raise
