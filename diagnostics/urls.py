from django.urls import path

from . import views

urlpatterns = [
    path('health/', views.health_check, name='diagnostics-health'),
    path('logs/', views.recent_logs, name='diagnostics-logs'),
]
