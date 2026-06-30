# apps/audit/urls.py
from django.urls import path
from apps.audit import views

urlpatterns = [
    path("", views.AuditLogListView.as_view(), name="audit-log-list"),
]