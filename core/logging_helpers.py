import json
import logging
from contextvars import ContextVar
from datetime import datetime
from typing import Any, Dict, Optional

request_id_var: ContextVar[Optional[str]] = ContextVar('request_id_var', default=None)


def set_request_id(request_id: Optional[str]) -> None:
    request_id_var.set(request_id)


def get_request_id() -> Optional[str]:
    return request_id_var.get()


class RequestIdFilter(logging.Filter):
    def filter(self, record: logging.LogRecord) -> bool:
        record.request_id = get_request_id()
        return True


class JsonFormatter(logging.Formatter):
    def format(self, record: logging.LogRecord) -> str:
        payload: Dict[str, Any] = {
            'timestamp': datetime.utcnow().isoformat(),
            'level': record.levelname,
            'logger': record.name,
            'message': record.getMessage(),
        }

        if getattr(record, 'request_id', None):
            payload['request_id'] = record.request_id

        if getattr(record, 'request_path', None):
            payload['request_path'] = record.request_path

        if getattr(record, 'request_method', None):
            payload['request_method'] = record.request_method

        if getattr(record, 'response_status', None):
            payload['response_status'] = record.response_status

        if getattr(record, 'duration_ms', None):
            payload['duration_ms'] = record.duration_ms

        if getattr(record, 'user_id', None):
            payload['user_id'] = record.user_id

        metadata = getattr(record, 'metadata', None)
        if metadata:
            payload['metadata'] = metadata

        events = getattr(record, 'events', None)
        if events:
            payload['events'] = events

        if record.args:
            payload['args'] = record.args

        if record.exc_info:
            payload['exception'] = self.formatException(record.exc_info)

        return json.dumps(payload, ensure_ascii=False, default=str)
