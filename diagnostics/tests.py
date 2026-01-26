from django.test import TestCase
from django.urls import reverse

from .models import DiagnosticLog


class DiagnosticsTests(TestCase):
    def test_health_check_view(self):
        response = self.client.get(reverse('diagnostics-health'))
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.json()['status'], 'ok')

    def test_middleware_logs_on_request(self):
        self.client.get(reverse('diagnostics-health'))
        self.assertTrue(DiagnosticLog.objects.exists())
