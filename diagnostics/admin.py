from django.contrib import admin

from .models import DiagnosticLog


@admin.register(DiagnosticLog)
class DiagnosticLogAdmin(admin.ModelAdmin):
    list_display = (
        'timestamp',
        'level',
        'logger_name',
        'request_method',
        'request_path',
        'response_status',
        'external_service',
    )
    list_filter = ('level', 'external_service')
    search_fields = ('message', 'logger_name', 'request_path')
    readonly_fields = ('timestamp',)
