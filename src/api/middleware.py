"""
API middleware for metrics, tracing, and request handling.
"""

import time
from fastapi import Request, Response
from starlette.middleware.base import BaseHTTPMiddleware
from src.core.metrics import request_count, request_duration
from src.core.logger import get_logger

logger = get_logger(__name__)


class MetricsMiddleware(BaseHTTPMiddleware):
    """Middleware to collect Prometheus metrics for each request."""

    async def dispatch(self, request: Request, call_next):
        start_time = time.time()
        method = request.method
        endpoint = request.url.path

        try:
            response = await call_next(request)
            status = str(response.status_code)
            return response
        except Exception as exc:
            status = "500"
            raise exc
        finally:
            duration = time.time() - start_time
            request_count.labels(method=method, endpoint=endpoint, status=status).inc()
            request_duration.labels(method=method, endpoint=endpoint).observe(duration)


class TimingMiddleware(BaseHTTPMiddleware):
    """Middleware to add X-Process-Time header."""

    async def dispatch(self, request: Request, call_next):
        start_time = time.time()
        response = await call_next(request)
        process_time = time.time() - start_time
        response.headers["X-Process-Time"] = str(process_time)
        return response


class LoggingMiddleware(BaseHTTPMiddleware):
    """Middleware to log all incoming requests."""

    async def dispatch(self, request: Request, call_next):
        start_time = time.time()
        client = request.client.host if request.client else None

        response = await call_next(request)
        process_time = time.time() - start_time

        logger.info(
            f"{request.method} {request.url.path} - {response.status_code} ({process_time:.3f}s)",
            extra={
                "method": request.method,
                "path": request.url.path,
                "status_code": response.status_code,
                "process_time": process_time,
                "client": client,
            }
        )
        return response
