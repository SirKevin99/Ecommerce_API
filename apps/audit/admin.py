# apps/audit/admin.py
from django.contrib import admin
from apps.audit.models import AuditLog


@admin.register(AuditLog)
class AuditLogAdmin(admin.ModelAdmin):
    list_display  = ["action", "user", "object_repr", "ip_address", "created_at"]
    list_filter   = ["action", "content_type"]
    search_fields = ["user__email", "object_repr", "ip_address"]
    readonly_fields = [
        "user", "action", "content_type", "object_id",
        "object_repr", "changes", "ip_address", "user_agent", "created_at"
    ]

    def has_add_permission(self, request):
        return False  # Los logs no se crean manualmente

    def has_delete_permission(self, request, obj=None):
        return False  # Los logs no se eliminan