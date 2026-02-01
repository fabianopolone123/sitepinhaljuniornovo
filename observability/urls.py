from django.urls import path

from . import views

urlpatterns = [
    path("client-logs/", views.client_logs, name="client_logs"),
]
