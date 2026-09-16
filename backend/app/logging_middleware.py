"""
Structured JSON logging middleware.
Logs: request_id, session_id (if present), active_provider, latency_ms, retrieval_hit_count.
"""
import time
import json
import uuid
import logging
import sys
from typing import Callable

from starlette.middleware.base import BaseHTTPMiddleware
from starlette.requests import Request
from starlette.responses import Response


class JSONFormatter(logging.Formatter):
    def format(self, record: logging.LogRecord) -> str:
        log: dict = {
            "timestamp": self.formatTime(record),
            "level": record.levelname,
            "logger": record.name,
            "message": record.getMessage(),
        }
        # Attach any extra fields passed by callers
        for key in ("request_id", "session_id", "provider", "latency_ms", "retrieval_hits", "status_code", "path"):
            if hasattr(record, key):
                log[key] = getattr(record, key)
        return json.dumps(log)


def configure_logging() -> None:
    root = logging.getLogger()
    root.setLevel(logging.INFO)
    if not root.handlers:
        handler = logging.StreamHandler(sys.stdout)
        handler.setFormatter(JSONFormatter())
        root.addHandler(handler)


logger = logging.getLogger("api")


class LoggingMiddleware(BaseHTTPMiddleware):
    async def dispatch(self, request: Request, call_next: Callable) -> Response:
        request_id = str(uuid.uuid4())
        request.state.request_id = request_id

        start = time.perf_counter()
        response = await call_next(request)
        latency_ms = round((time.perf_counter() - start) * 1000, 2)

        import os
        provider = os.environ.get("LLM_PROVIDER", "groq")

        # session_id extracted from path if present, e.g. /api/sessions/42/...
        session_id = None
        parts = request.url.path.split("/")
        if "sessions" in parts:
            idx = parts.index("sessions")
            if idx + 1 < len(parts) and parts[idx + 1].isdigit():
                session_id = int(parts[idx + 1])

        logger.info(
            f"{request.method} {request.url.path} → {response.status_code}",
            extra={
                "request_id": request_id,
                "session_id": session_id,
                "provider": provider,
                "latency_ms": latency_ms,
                "status_code": response.status_code,
                "path": request.url.path,
            },
        )
        response.headers["X-Request-ID"] = request_id
        return response
