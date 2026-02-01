import json
import logging

from django.http import JsonResponse
from django.views.decorators.csrf import csrf_exempt
from django.views.decorators.http import require_POST

from core.logging_helpers import get_request_id

client_logger = logging.getLogger("client_logs")
MAX_EVENTS = 40
MAX_EVENT_SIZE = 2048
SENSITIVE_SUBSTRINGS = ("password", "token", "secret", "cookie", "auth")


def _truncate(value):
    text = str(value or "")
    trimmed = text.replace("\n", " ").strip()
    if len(trimmed) > MAX_EVENT_SIZE:
        return trimmed[: MAX_EVENT_SIZE - 1] + "…"
    return trimmed


def _is_sensitive(key):
    if not isinstance(key, str):
        return False
    lowered = key.lower()
    return any(token in lowered for token in SENSITIVE_SUBSTRINGS)


def _sanitize_event(event):
    if not isinstance(event, dict):
        return {"value": _truncate(str(event))}
    sanitized = {}
    for key, value in event.items():
        if _is_sensitive(key):
            sanitized[key] = "<redacted>"
            continue
        sanitized[key] = _truncate(value if value is not None else "")
    return sanitized


def _capture_events(events):
    sanitized = []
    for raw in events:
        sanitized.append(_sanitize_event(raw))
        if len(sanitized) >= MAX_EVENTS:
            break
    return sanitized


@csrf_exempt
@require_POST
def client_logs(request):
    try:
        payload = json.loads(request.body.decode("utf-8"))
    except json.JSONDecodeError:
        return JsonResponse({"detail": "JSON inválido"}, status=400)

    events = payload.get("events") or []
    if not isinstance(events, list):
        return JsonResponse({"detail": "events deve ser uma lista"}, status=400)

    batch = _capture_events(events)
    if not batch:
        return JsonResponse({"detail": "sem eventos válidos"}, status=400)

    request_id = payload.get("request_id") or get_request_id()
    session_id = payload.get("session_id")
    client_logger.info(
        "Client browser log",
        extra={
            "request_id": request_id,
            "metadata": {
                "session_id": session_id,
                "event_count": len(batch),
                "truncated": len(events) > MAX_EVENTS,
                "remote_addr": request.META.get("REMOTE_ADDR"),
                "user_id": getattr(request.user, "id", None),
            },
            "events": batch,
        },
    )
    return JsonResponse({"status": "ok"})
