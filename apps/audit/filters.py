# apps/audit/filters.py
import django_filters
from apps.audit.models import AuditLog


class AuditLogFilter(django_filters.FilterSet):
    user       = django_filters.CharFilter(field_name="user__email", lookup_expr="icontains")
    action     = django_filters.ChoiceFilter(choices=AuditLog.Action.choices)
    date_from  = django_filters.DateTimeFilter(field_name="created_at", lookup_expr="gte")
    date_until = django_filters.DateTimeFilter(field_name="created_at", lookup_expr="lte")
    model      = django_filters.CharFilter(field_name="content_type__model", lookup_expr="exact")

    class Meta:
        model  = AuditLog
        fields = ["user", "action", "date_from", "date_until", "model"]