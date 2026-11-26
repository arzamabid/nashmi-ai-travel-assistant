
import logging
import time
import uuid

from fastapi import Request
from starlette.middleware.base import BaseHTTPMiddleware


logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s %(levelname)s %(message)s",
)

logger = logging.getLogger("nashmi.api")


class RequestLoggingMiddleware(BaseHTTPMiddleware):
    async def dispatch(self, request: Request, call_next):
        request_id = str(uuid.uuid4())
        start = time.perf_counter()

        try:
            response = await call_next(request)
        except Exception:
            duration_ms = round(
                (time.perf_counter() - start) * 1000,
                2,
            )

            logger.exception(
                "request_failed request_id=%s method=%s "
                "path=%s duration_ms=%s",
                request_id,
                request.method,
                request.url.path,
                duration_ms,
            )
            raise

        duration_ms = round(
            (time.perf_counter() - start) * 1000,
            2,
        )

        logger.info(
            "request_completed request_id=%s method=%s "
            "path=%s status=%s duration_ms=%s",
            request_id,
            request.method,
            request.url.path,
            response.status_code,
            duration_ms,
        )

        response.headers["X-Request-ID"] = request_id
        return response
