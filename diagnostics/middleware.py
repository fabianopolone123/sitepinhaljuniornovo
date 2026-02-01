import logging
import time

from core.logging_helpers import get_request_id


class DiagnosticLoggingMiddleware:
    """Middleware that logs each incoming request/response cycle."""

    def __init__(self, get_response):
        self.get_response = get_response
        self.logger = logging.getLogger('diagnostics.middleware')

    def __call__(self, request):
        start = time.monotonic()
        response = self.get_response(request)
        duration_ms = int((time.monotonic() - start) * 1000)
        self.logger.info(
            'HTTP request completed',
            extra={
                'metadata': {
                    'remote_addr': request.META.get('REMOTE_ADDR'),
                },
                'request_method': request.method,
                'request_path': request.get_full_path(),
                'response_status': response.status_code,
                'duration_ms': duration_ms,
                'request_id': get_request_id(),
                'user_id': getattr(request.user, 'id', None),
            },
        )
        return response
