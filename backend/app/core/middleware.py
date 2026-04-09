import logging

from starlette.middleware.base import BaseHTTPMiddleware
from starlette.requests import Request

logger = logging.getLogger(__name__)


class RequestLoggingMiddleware(BaseHTTPMiddleware):
    async def dispatch(self, request: Request, call_next):
        try:
            response = await call_next(request)
            logger.info(
                f"Request: {request.method} {request.url} | "
                f"Response: {response.status_code}"
            )
            return response
        except Exception as e:
            logger.error(
                f"Request: {request.method} {request.url} | "
                f"Failed with exception: {e}"
            )
            raise
