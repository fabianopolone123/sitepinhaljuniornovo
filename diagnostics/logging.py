import logging

from django.db.utils import OperationalError, ProgrammingError


class DatabaseLogHandler(logging.Handler):
    """Handler that writes log records into the diagnostic audit table."""

    def emit(self, record):
        from django.db import transaction

        metadata = dict(getattr(record, 'metadata', {}) or {})
        log_fields = {
            'level': record.levelname,
            'logger_name': record.name,
            'message': record.getMessage(),
            'metadata': metadata or None,
            'details': getattr(record, 'details', None),
            'external_service': getattr(record, 'external_service', None),
            'request_path': getattr(record, 'request_path', metadata.get('request_path')),
            'request_method': getattr(record, 'request_method', metadata.get('request_method')),
            'response_status': getattr(record, 'response_status', metadata.get('response_status')),
            'duration_ms': getattr(record, 'duration_ms', metadata.get('duration_ms')),
        }

        try:
            with transaction.atomic():
                from .models import DiagnosticLog

                DiagnosticLog.objects.create(**log_fields)
        except (OperationalError, ProgrammingError):
            return
        except Exception:
            self.handleError(record)
