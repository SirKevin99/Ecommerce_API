# apps/audit/views.py
from rest_framework import generics
from rest_framework.permissions import IsAdminUser
from django_filters.rest_framework import DjangoFilterBackend
from rest_framework.filters import SearchFilter, OrderingFilter

from apps.audit.models import AuditLog
from apps.audit.serializers import AuditLogSerializer
from apps.audit.filters import AuditLogFilter


class AuditLogListView(generics.ListAPIView):
    """
    GET → lista el historial de auditoría completo.
    Solo accesible para admins.
    Permite filtrar por usuario, acción y rango de fechas.
    """
    serializer_class   = AuditLogSerializer
    permission_classes = [IsAdminUser]
    queryset           = AuditLog.objects.select_related(
                           "user", "content_type"
                         ).all()
    filter_backends    = [DjangoFilterBackend, SearchFilter, OrderingFilter]
    filterset_class    = AuditLogFilter
    search_fields      = ["user__email", "object_repr"]
    ordering_fields    = ["created_at"]
    ordering           = ["-created_at"]