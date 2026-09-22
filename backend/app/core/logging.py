import logging
import sys
import time
import uuid

from starlette.middleware.base import BaseHTTPMiddleware
from starlette.requests import Request

from app.config import settings

logger = logging.getLogger("signalwork")


def configure_logging() -> None:
    handler = logging.StreamHandler(sys.stdout)
    formatter = logging.Formatter(
        fmt="%(asctime)s %(levelname)s %(name)s request_id=%(request_id)s %(message)s",
        defaults={"request_id": "-"},
    )
    handler.setFormatter(formatter)
    root = logging.getLogger()
    root.handlers = [handler]
    root.setLevel(settings.log_level)


class RequestContextMiddleware(BaseHTTPMiddleware):
    """
    Assigns a request ID to every request (propagated via X-Request-ID),
    logs method/path/status/duration, and turns any unhandled exception
    into a clean 500 instead of leaking a stack trace to the client.
    """

    async def dispatch(self, request: Request, call_next):
        request_id = request.headers.get("X-Request-ID", str(uuid.uuid4()))
        start = time.perf_counter()
        extra = {"request_id": request_id}

        try:
            response = await call_next(request)
        except Exception:
            duration_ms = round((time.perf_counter() - start) * 1000, 2)
            logger.exception(
                "unhandled_exception method=%s path=%s duration_ms=%s",
                request.method,
                request.url.path,
                duration_ms,
                extra=extra,
            )
            raise

        duration_ms = round((time.perf_counter() - start) * 1000, 2)
        logger.info(
            "request_complete method=%s path=%s status=%s duration_ms=%s",
            request.method,
            request.url.path,
            response.status_code,
            duration_ms,
            extra=extra,
        )
        response.headers["X-Request-ID"] = request_id
        return response
