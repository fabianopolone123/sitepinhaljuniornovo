from django.core import signing
from django.http import JsonResponse
from django.views.decorators.http import require_GET

from .models import DiagnosticLog


@require_GET
def health_check(request):
    """Simple endpoint to validate the site is reachable."""

    return JsonResponse(
        {
            'status': 'ok',
            'domain': 'pinhaljunior.com.br',
            'diagnostics_token': signing.dumps({'path': request.path}),
        }
    )


@require_GET
def recent_logs(request):
    """Return a small slice of the latest diagnostic records for quick‑checks."""

    logs = DiagnosticLog.objects.all()[:20]
    return JsonResponse(
        {
            'logs': [
                {
                    'timestamp': log.timestamp.isoformat(),
                    'level': log.level,
                    'message': log.message,
                    'request_path': log.request_path,
                    'response_status': log.response_status,
                    'external_service': log.external_service,
                }
                for log in logs
            ]
        }
    )
