import logging
import time
import uuid

from .logging_helpers import get_request_id, set_request_id


class RequestIdMiddleware:
    """Ensures every request carries a stable request_id."""

    def __init__(self, get_response):
        self.get_response = get_response

    def __call__(self, request):
        incoming = (
            request.headers.get("X-Request-ID")
            or request.META.get("HTTP_X_REQUEST_ID")
            or str(uuid.uuid4())
        )
        request.request_id = incoming
        set_request_id(incoming)
        try:
            response = self.get_response(request)
        finally:
            set_request_id(None)
        response.setdefault("X-Request-ID", incoming)
        return response


class RequestLoggingMiddleware:
    """Logs request lifecycle details with duration and request_id."""

    def __init__(self, get_response):
        self.get_response = get_response
        self.logger = logging.getLogger("core.requests")

    def __call__(self, request):
        start = time.monotonic()
        response = self.get_response(request)
        duration_ms = int((time.monotonic() - start) * 1000)
        self.logger.info(
            "Request completed",
            extra={
                "request_id": get_request_id(),
                "request_method": request.method,
                "request_path": request.get_full_path(),
                "response_status": response.status_code,
                "duration_ms": duration_ms,
                "metadata": {
                    "remote_addr": request.META.get("REMOTE_ADDR"),
                    "user_agent": request.META.get("HTTP_USER_AGENT"),
                    "request_id": getattr(request, "request_id", None),
                },
            },
        )
        return response
