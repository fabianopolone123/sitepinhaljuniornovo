from django.db import models


class DiagnosticLog(models.Model):
    timestamp = models.DateTimeField(auto_now_add=True)
    level = models.CharField(max_length=10)
    logger_name = models.CharField(max_length=255)
    message = models.TextField()
    metadata = models.JSONField(blank=True, null=True)
    request_path = models.CharField(max_length=2048, blank=True, null=True)
    request_method = models.CharField(max_length=10, blank=True, null=True)
    response_status = models.PositiveIntegerField(blank=True, null=True)
    duration_ms = models.PositiveIntegerField(blank=True, null=True)
    external_service = models.CharField(max_length=255, blank=True, null=True)
    details = models.JSONField(blank=True, null=True)

    class Meta:
        ordering = ['-timestamp']

    def __str__(self):
        return (
            f"[{self.timestamp.isoformat()}] {self.level} {self.logger_name} "
            f"{self.request_method or ''} {self.request_path or ''}"
        )
